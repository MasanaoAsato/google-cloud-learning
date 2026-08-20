#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from inspect_drawio import graph_inventory, local_name, read_graph_model, read_mxfile


def load_spec(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read specification: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("specification root must be an object")
    return data


def rectangle(cell: dict[str, Any]) -> tuple[float, float, float, float] | None:
    geometry = cell.get("geometry")
    if not isinstance(geometry, dict):
        return None
    try:
        x = float(geometry.get("x", 0))
        y = float(geometry.get("y", 0))
        width = float(geometry["width"])
        height = float(geometry["height"])
    except (KeyError, TypeError, ValueError):
        return None
    return x, y, width, height


def overlaps(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> bool:
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def absolute_rectangle(
    cell: dict[str, Any],
    by_id: dict[str, dict[str, Any]],
) -> tuple[float, float, float, float] | None:
    rect = rectangle(cell)
    if rect is None:
        return None
    x, y, width, height = rect
    parent_id = cell.get("parent")
    seen = {cell.get("id")}
    while parent_id in by_id and parent_id not in seen:
        seen.add(parent_id)
        parent = by_id[parent_id]
        parent_rect = rectangle(parent)
        if parent_rect is None:
            break
        x += parent_rect[0]
        y += parent_rect[1]
        parent_id = parent.get("parent")
    return x, y, width, height


def validate_drawio(spec: dict[str, Any], drawio: Path) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        mxfile = read_mxfile(drawio)
        model = read_graph_model(mxfile)
        inventory = graph_inventory(model)
    except ValueError as exc:
        return [str(exc)], warnings, {}

    cells = inventory["cells"]
    by_id = {cell["id"]: cell for cell in cells if cell.get("id")}
    ids = set(by_id)
    required = {item["id"] for field in ("containers", "nodes", "edges") for item in spec.get(field, [])}
    missing = sorted(required - ids)
    if missing:
        errors.append(f"draw.io is missing specification IDs: {', '.join(missing)}")

    for cell in cells:
        if cell.get("edge"):
            if cell.get("source") not in ids:
                errors.append(f"edge {cell['id']!r} has unknown source {cell.get('source')!r}")
            if cell.get("target") not in ids:
                errors.append(f"edge {cell['id']!r} has unknown target {cell.get('target')!r}")
        style = cell.get("style", "")
        if "image=http://" in style or "image=https://" in style:
            errors.append(f"cell {cell['id']!r} references an external image URL")

    show_all_addresses = bool(spec.get("show_terraform_addresses", False))
    for node in spec.get("nodes", []):
        node_id = node.get("id")
        address = node.get("terraform_address", "")
        if not node_id or not address or show_all_addresses or node.get("show_terraform_address", False):
            continue
        visible_values = [
            html.unescape(cell.get("value", ""))
            for cell in cells
            if cell.get("id") == node_id or cell.get("parent") == node_id
        ]
        if any(address in value for value in visible_values):
            errors.append(f"Terraform address is visible without opt-in on node {node_id!r}")

    # Every node is an icon card, including people and networks drawn outside the
    # cloud: a diagram where only some subjects have icons reads as unfinished.
    for node in spec.get("nodes", []):
        node_id = node.get("id")
        card = by_id.get(node_id)
        icon = by_id.get(f"{node_id}__icon")
        label = by_id.get(f"{node_id}__label")
        if card is None or "container=1" not in card.get("style", ""):
            errors.append(f"node {node_id!r} is not an icon card")
        if icon is None or icon.get("data_kind") != "node-icon":
            errors.append(f"node {node_id!r} has no icon cell")
        elif (
            "shape=image" not in icon.get("style", "")
            and "shape=mxgraph." not in icon.get("style", "")
            and "placeholderIcon=1" not in icon.get("style", "")
        ):
            errors.append(f"node {node_id!r} does not use a Draw.io stencil or image icon")
        if label is None or label.get("data_kind") != "node-label":
            errors.append(f"node {node_id!r} has no label cell")

    # A boundary name painted across its own border is the least readable text in
    # the picture, so the builder gives every container a label cell inside it.
    for container in spec.get("containers", []):
        container_id = container.get("id")
        cell = by_id.get(container_id)
        label = by_id.get(f"{container_id}__label")
        style = cell.get("style", "") if cell is not None else ""
        # 境界は直角が原則。例外はGCP公式Zoneが使う枠線なし・カードと同じ2pxの微小な角丸だけ。
        gcp_zone_corner = "strokeColor=none" in style and "absoluteArcSize=1" in style and "arcSize=2" in style
        if cell is not None and "rounded=0" not in style and not gcp_zone_corner:
            errors.append(f"container {container_id!r} does not use square corners")
        if cell is not None and cell.get("value"):
            errors.append(
                f"container {container_id!r} carries its own label value; the label belongs in "
                f"{container_id}__label so it cannot land on the border"
            )
        if label is None or label.get("data_kind") != "container-label":
            errors.append(f"container {container_id!r} has no label cell")

    siblings: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    for cell in cells:
        if cell.get("data_kind") == "node" and rectangle(cell):
            siblings[cell.get("parent")].append(cell)
    for parent, group in siblings.items():
        for index, first in enumerate(group):
            for second in group[index + 1 :]:
                if overlaps(rectangle(first), rectangle(second)):  # type: ignore[arg-type]
                    errors.append(
                        f"nodes overlap under parent {parent!r}: {first['id']!r} and {second['id']!r}"
                    )

    containers = {cell["id"]: cell for cell in cells if cell.get("data_kind") == "container"}
    for cell in cells:
        parent_id = cell.get("parent")
        if parent_id not in by_id or not cell.get("vertex"):
            continue
        child_rect = rectangle(cell)
        parent_rect = rectangle(by_id[parent_id])
        if child_rect is None or parent_rect is None:
            continue
        x, y, width, height = child_rect
        _, _, parent_width, parent_height = parent_rect
        if x < 0 or y < 0 or x + width > parent_width or y + height > parent_height:
            errors.append(f"cell {cell['id']!r} extends outside parent {parent_id!r}")

    canvas_width = float(model.attrib.get("pageWidth", spec.get("canvas", {}).get("width", 0)))
    canvas_height = float(model.attrib.get("pageHeight", spec.get("canvas", {}).get("height", 0)))
    for cell in cells:
        if not cell.get("vertex"):
            continue
        rect = absolute_rectangle(cell, by_id)
        if rect is None:
            continue
        x, y, width, height = rect
        if x < 0 or y < 0 or x + width > canvas_width or y + height > canvas_height:
            errors.append(f"cell {cell['id']!r} extends outside canvas")

    legends = [cell for cell in cells if cell.get("data_kind") == "legend"]
    top_level_content = [
        cell
        for cell in cells
        if cell.get("data_kind") in {"node", "container"}
        and str(cell.get("parent", "")).startswith("layer-")
    ]
    for legend in legends:
        legend_rect = absolute_rectangle(legend, by_id)
        if legend_rect is None:
            continue
        for cell in top_level_content:
            content_rect = absolute_rectangle(cell, by_id)
            if content_rect is not None and overlaps(legend_rect, content_rect):
                errors.append(f"legend overlaps top-level element {cell['id']!r}")

    if not any(cell.get("data_kind") == "legend" for cell in cells) and spec.get("edges"):
        warnings.append("diagram has edges but no generated legend")
    return errors, warnings, inventory


def validate_svg(
    path: Path,
    drawio_inventory: dict[str, Any],
    required_ids: set[str],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.exists() or path.stat().st_size == 0:
        return [f"SVG is missing or empty: {path}"], warnings
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"SVG XML is invalid: {exc}"], warnings
    if local_name(root.tag) != "svg":
        errors.append(f"SVG root element is {local_name(root.tag)!r}, expected 'svg'")
    if "viewBox" not in root.attrib:
        warnings.append("SVG has no viewBox")
    if "content" not in root.attrib:
        warnings.append("SVG has no embedded draw.io content attribute")
    else:
        try:
            mxfile = read_mxfile(path)
            model = read_graph_model(mxfile)
            svg_inventory = graph_inventory(model)
        except ValueError as exc:
            errors.append(f"embedded draw.io content is invalid: {exc}")
        else:
            svg_cells = {cell["id"]: cell for cell in svg_inventory["cells"] if cell.get("id")}
            drawio_cells = {
                cell["id"]: cell for cell in drawio_inventory.get("cells", []) if cell.get("id")
            }
            missing = sorted(required_ids - svg_cells.keys())
            if missing:
                errors.append(f"SVG embedded diagram is missing specification IDs: {', '.join(missing)}")
            for item_id in sorted(required_ids & svg_cells.keys() & drawio_cells.keys()):
                for field in ("value", "source", "target", "terraform_address", "evidence_status"):
                    if svg_cells[item_id].get(field) != drawio_cells[item_id].get(field):
                        errors.append(
                            f"SVG embedded diagram differs from draw.io for {item_id!r} field {field!r}"
                        )
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate draw.io and SVG architecture artifacts")
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--drawio", type=Path, required=True)
    parser.add_argument("--svg", type=Path)
    args = parser.parse_args()

    try:
        spec = load_spec(args.spec)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    errors, warnings, inventory = validate_drawio(spec, args.drawio)
    if args.svg:
        required_ids = {
            item["id"]
            for field in ("containers", "nodes", "edges")
            for item in spec.get(field, [])
        }
        svg_errors, svg_warnings = validate_svg(args.svg, inventory, required_ids)
        errors.extend(svg_errors)
        warnings.extend(svg_warnings)

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print(f"artifact validation failed: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(
        "artifact validation passed: "
        f"{inventory.get('vertex_count', 0)} vertices, "
        f"{inventory.get('edge_count', 0)} edges, "
        f"{len(warnings)} warning(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
