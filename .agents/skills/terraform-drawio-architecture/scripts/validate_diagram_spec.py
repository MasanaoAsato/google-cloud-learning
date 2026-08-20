#!/usr/bin/env python3

"""Validate the intermediate diagram specification before anything is drawn.

Beyond schema checks, this enforces the layout contract that decides whether the
finished picture is readable: every node resolves to a real Draw.io icon, labels
fit inside their cards, boundaries keep enough room for their own name, and
containers are neither cramped nor mostly empty. Catching those here is much
cheaper than discovering them in an exported image.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import layout as layout_engine
import text_layout
from icon_catalog import IconCatalog

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TOKENS = SKILL_DIR / "assets" / "style-tokens.json"

ROOT_REQUIRED = {
    "schema_version",
    "title",
    "provider",
    "source_roots",
    "canvas",
    "containers",
    "nodes",
    "edges",
    "omissions",
    "unresolved",
}
PROVIDERS = {"aws", "azure", "gcp", "multi"}
ITEM_PROVIDERS = {"aws", "azure", "gcp", "neutral"}
STATUSES = {"confirmed", "derived", "unresolved"}
EDGE_KINDS = {
    "traffic",
    "async",
    "peer",
    "control",
    "dependency",
    "special",
}
BOUNDARY_KINDS = {"cloud", "organization", "account", "subscription", "project"}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("root must be a JSON object")
    return data


def load_tokens(path: Path = DEFAULT_TOKENS) -> dict[str, Any]:
    return load_json(path)


def valid_geometry(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    for key in ("x", "y", "width", "height"):
        number = value.get(key)
        if not isinstance(number, (int, float)) or isinstance(number, bool):
            return False
        if not math.isfinite(number):
            return False
    return value["x"] >= 0 and value["y"] >= 0 and value["width"] > 0 and value["height"] > 0


def check_evidence(value: Any, context: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{context}: evidence must contain at least one item")
        return
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{context}.evidence[{index}]: must be an object")
            continue
        if not isinstance(item.get("source"), str) or not item["source"].strip():
            errors.append(f"{context}.evidence[{index}]: source is required")
        if not isinstance(item.get("note"), str) or not item["note"].strip():
            errors.append(f"{context}.evidence[{index}]: note is required")
        if "line" in item and (not isinstance(item["line"], int) or item["line"] < 1):
            errors.append(f"{context}.evidence[{index}]: line must be a positive integer")


def check_grid(geometry: dict[str, Any], context: str, warnings: list[str]) -> None:
    for key in ("x", "y", "width", "height"):
        if geometry[key] % 10 != 0:
            warnings.append(f"{context}: geometry.{key}={geometry[key]} is not on the 10px grid")


def rectangles_overlap(first: dict[str, Any], second: dict[str, Any]) -> bool:
    return (
        first["x"] < second["x"] + second["width"]
        and first["x"] + first["width"] > second["x"]
        and first["y"] < second["y"] + second["height"]
        and first["y"] + first["height"] > second["y"]
    )


def separation(first: dict[str, Any], second: dict[str, Any]) -> float:
    gap_x = max(second["x"] - (first["x"] + first["width"]), first["x"] - (second["x"] + second["width"]))
    gap_y = max(second["y"] - (first["y"] + first["height"]), first["y"] - (second["y"] + second["height"]))
    return max(gap_x, gap_y)


def bounding_box(rects: list[dict[str, Any]]) -> dict[str, float]:
    left = min(rect["x"] for rect in rects)
    top = min(rect["y"] for rect in rects)
    right = max(rect["x"] + rect["width"] for rect in rects)
    bottom = max(rect["y"] + rect["height"] for rect in rects)
    return {"x": left, "y": top, "width": right - left, "height": bottom - top}


def check_shared_fields(
    item: dict[str, Any], context: str, errors: list[str], warnings: list[str]
) -> bool:
    """Check the fields every container and node carries.

    Returns True when the geometry is usable, so the caller can decide whether to
    add the item to the layout index for the overlap and padding checks.
    """
    if item.get("provider") not in ITEM_PROVIDERS:
        errors.append(f"{context}: invalid provider")
    if item.get("status") not in STATUSES:
        errors.append(f"{context}: invalid status")
    if not isinstance(item.get("label"), str) or not item["label"].strip():
        errors.append(f"{context}: label is required")
    check_evidence(item.get("evidence"), context, errors)
    if not valid_geometry(item.get("geometry")):
        errors.append(f"{context}: invalid geometry")
        return False
    check_grid(item["geometry"], context, warnings)
    return True


def check_icons(
    nodes: list[dict[str, Any]],
    diagram_provider: str | None,
    errors: list[str],
    warnings: list[str],
) -> None:
    """Prefer a real icon for every node; a plain box is the accepted last resort.

    A broken catalog is an error, but a service without an icon is only a
    warning: the builder will draw a plain box with the service name, and the
    fallback belongs in architecture-notes.md.
    """
    try:
        catalog = IconCatalog.load()
    except ValueError as exc:
        errors.append(f"icon catalog unusable: {exc}")
        return
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue
        if (node.get("shape_style") or "").strip():
            continue
        service = node.get("service", "")
        if not isinstance(service, str) or not service.strip():
            continue
        provider = node.get("provider")
        if provider not in {"aws", "azure", "gcp"}:
            provider = diagram_provider
        try:
            catalog.resolve(service, provider)
        except KeyError:
            suggestions = catalog.suggest(service)
            hint = f" Closest catalog names: {', '.join(suggestions)}." if suggestions else ""
            warnings.append(
                f"nodes[{index}]: no Draw.io icon for service {service!r}; it will be drawn "
                f"as a plain box with the service name.{hint} Use a catalog name, fetch the "
                "icon with maintenance/sync_sidebar_icons.py, or keep the box and record "
                "the fallback in architecture-notes.md"
            )


def check_labels(
    spec: dict[str, Any],
    tokens: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    layout = tokens["geometry"]
    typography = tokens["typography"]
    for index, node in enumerate(spec.get("nodes", [])):
        if not isinstance(node, dict) or not valid_geometry(node.get("geometry")):
            continue
        geometry = node["geometry"]
        context = f"nodes[{index}] ({node.get('id')})"
        if geometry["width"] < layout["min_card_width"] or geometry["height"] < layout["min_card_height"]:
            errors.append(
                f"{context}: icon cards must be at least "
                f"{layout['min_card_width']:g}x{layout['min_card_height']:g}px so the icon, name "
                "and role all fit with padding"
            )
            continue
        text_width = (
            geometry["width"]
            - 2 * layout["card_padding_x"]
            - layout["icon_size"]
            - layout["card_icon_gap"]
        )
        text_height = geometry["height"] - 2 * layout["card_padding_y"]
        used = 0.0
        for value, size, bold in (
            (node.get("label", ""), typography["service_size"], True),
            ((node.get("role") or ""), typography["note_size"], False),
        ):
            if not value:
                continue
            lines = text_layout.wrap(value, text_width, size, bold=bold)
            used += len(lines) * text_layout.line_height(size)
        if node.get("status") == "unresolved":
            used += text_layout.line_height(typography["note_size"])
        if used > text_height + 0.5:
            errors.append(
                f"{context}: name and role wrap to {used:.0f}px of text but the card offers "
                f"{text_height:.0f}px. Widen or heighten the card, or shorten the role"
            )

    for index, container in enumerate(spec.get("containers", [])):
        if not isinstance(container, dict) or not valid_geometry(container.get("geometry")):
            continue
        size = (
            typography["boundary_size"]
            if container.get("kind") in BOUNDARY_KINDS
            else typography["sub_boundary_size"]
        )
        available = container["geometry"]["width"] - 2 * layout["label_inset"]
        lines = text_layout.wrap(container.get("label", ""), available, size, bold=True)
        needed = 12 + len(lines) * text_layout.line_height(size) + 8
        if needed > layout["container_header"] + 0.5:
            errors.append(
                f"containers[{index}] ({container.get('id')}): the label needs {len(lines)} line(s) "
                f"({needed:.0f}px) but the header band is {layout['container_header']:g}px. Widen the "
                "container so the name fits on one line, or shorten the label"
            )


def check_padding(
    spec: dict[str, Any],
    tokens: dict[str, Any],
    geometries: dict[str, dict[str, Any]],
    layout_parents: dict[str, str | None],
    errors: list[str],
    warnings: list[str],
    legend_rect: dict[str, Any] | None = None,
) -> None:
    """Boundaries need room for their label and air around their content."""
    layout = tokens["geometry"]
    children: dict[str | None, list[str]] = {}
    for item_id, parent in layout_parents.items():
        children.setdefault(parent, []).append(item_id)

    container_ids = {item["id"] for item in spec.get("containers", []) if isinstance(item, dict)}
    for parent_id, group in children.items():
        rects = [geometries[item_id] for item_id in group if item_id in geometries]
        # The legend occupies canvas space, so it silences the unused-space
        # warning for the area reserved under the content. It does not tighten
        # the minimum-padding errors: authors may butt it against the margin.
        slack_rects = rects + [legend_rect] if parent_id is None and legend_rect else rects
        if not rects:
            continue
        box = bounding_box(rects)
        if parent_id is None:
            width = spec["canvas"]["width"]
            height = spec["canvas"]["height"]
            top_min = 90.0  # keep clear of the title block
            side_min = float(layout["outer_padding"])
            label = "canvas"
        elif parent_id in container_ids:
            parent = geometries[parent_id]
            width, height = parent["width"], parent["height"]
            top_min = float(layout["container_header"])
            side_min = float(layout["container_padding"])
            label = f"container {parent_id!r}"
        else:
            continue

        gaps = {
            "top": box["y"],
            "left": box["x"],
            "right": width - (box["x"] + box["width"]),
            "bottom": height - (box["y"] + box["height"]),
        }
        for side, minimum in (
            ("top", top_min),
            ("left", side_min),
            ("right", side_min),
            ("bottom", side_min),
        ):
            if gaps[side] < minimum - 0.5:
                errors.append(
                    f"{label}: only {gaps[side]:.0f}px of padding on the {side}, need "
                    f"{minimum:g}px. Cramped frames read as a table, not an architecture"
                )
        slack = float(layout["container_slack_warn"])
        slack_box = bounding_box(slack_rects)
        slack_gaps = {
            "top": slack_box["y"],
            "left": slack_box["x"],
            "right": width - (slack_box["x"] + slack_box["width"]),
            "bottom": height - (slack_box["y"] + slack_box["height"]),
        }
        for side, minimum in (
            ("top", top_min),
            ("left", side_min),
            ("right", side_min),
            ("bottom", side_min),
        ):
            if slack_gaps[side] > minimum + slack:
                warnings.append(
                    f"{label}: {slack_gaps[side]:.0f}px of unused space on the {side}. Shrink the frame "
                    "or move content into it so the whitespace is not read as a missing element"
                )


FLOW_KINDS = {"traffic", "async", "special"}


def check_flow(
    data: dict[str, Any],
    geometries: dict[str, dict[str, Any]],
    layout_parents: dict[str, str | None],
    warnings: list[str],
) -> None:
    """The processing path should read in one direction.

    Management and dependency edges may run wherever they need to, but a main
    path (traffic, async, special) that doubles back against the declared flow
    is what turns a diagram into spaghetti. Reversals are warnings, not errors:
    a deliberate loop (retry, callback) can stay once it is a conscious choice.
    """
    flow = data.get("flow", "horizontal")

    def center(item_id: str) -> tuple[float, float]:
        geometry = geometries[item_id]
        x = geometry["x"] + geometry["width"] / 2
        y = geometry["y"] + geometry["height"] / 2
        parent = layout_parents.get(item_id)
        while parent is not None and parent in geometries:
            x += geometries[parent]["x"]
            y += geometries[parent]["y"]
            parent = layout_parents.get(parent)
        return x, y

    for index, edge in enumerate(data.get("edges", [])):
        if not isinstance(edge, dict) or edge.get("kind") not in FLOW_KINDS:
            continue
        if edge.get("bidirectional"):
            continue
        source, target = edge.get("from"), edge.get("to")
        if source not in geometries or target not in geometries:
            continue
        source_center, target_center = center(source), center(target)
        along = (
            target_center[0] - source_center[0]
            if flow == "horizontal"
            else target_center[1] - source_center[1]
        )
        if along < -0.5:
            direction = "right to left" if flow == "horizontal" else "bottom to top"
            warnings.append(
                f"edges[{index}] ({edge.get('id')}): a main path runs against the {flow} flow "
                f"({source!r} -> {target!r} goes {direction}). Reorder grid cells so the "
                "processing direction advances one way, or declare flow: 'vertical' if the "
                "diagram genuinely reads top to bottom"
            )


def validate(data: dict[str, Any], tokens: dict[str, Any] | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if tokens is None:
        try:
            tokens = load_tokens()
        except ValueError as exc:
            return [str(exc)], warnings

    missing = ROOT_REQUIRED - data.keys()
    if missing:
        errors.append(f"missing root fields: {', '.join(sorted(missing))}")

    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(data.get("title"), str) or not data.get("title", "").strip():
        errors.append("title must be a non-empty string")
    if data.get("provider") not in PROVIDERS:
        errors.append(f"provider must be one of {sorted(PROVIDERS)}")
    if "flow" in data and data["flow"] not in {"horizontal", "vertical"}:
        errors.append("flow must be 'horizontal' or 'vertical'")
    if not isinstance(data.get("source_roots"), list) or not data.get("source_roots"):
        errors.append("source_roots must contain at least one path")

    canvas = data.get("canvas")
    if not isinstance(canvas, dict):
        errors.append("canvas must be an object")
    else:
        if not isinstance(canvas.get("width"), int) or canvas["width"] < 400:
            errors.append("canvas.width must be an integer >= 400")
        if not isinstance(canvas.get("height"), int) or canvas["height"] < 300:
            errors.append("canvas.height must be an integer >= 300")

    containers = data.get("containers", [])
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    for field, value in (("containers", containers), ("nodes", nodes), ("edges", edges)):
        if not isinstance(value, list):
            errors.append(f"{field} must be an array")

    if errors and not all(isinstance(value, list) for value in (containers, nodes, edges)):
        return errors, warnings

    ids: set[str] = set()
    container_ids: set[str] = set()
    node_ids: set[str] = set()
    parents: dict[str, str | None] = {}
    geometries: dict[str, dict[str, Any]] = {}
    layout_parents: dict[str, str | None] = {}
    layout_kinds: dict[str, str] = {}

    for index, container in enumerate(containers):
        context = f"containers[{index}]"
        if not isinstance(container, dict):
            errors.append(f"{context}: must be an object")
            continue
        item_id = container.get("id")
        if not isinstance(item_id, str) or not item_id:
            errors.append(f"{context}: id is required")
            continue
        if item_id in ids:
            errors.append(f"{context}: duplicate id {item_id!r}")
        ids.add(item_id)
        container_ids.add(item_id)
        parents[item_id] = container.get("parent")
        if check_shared_fields(container, context, errors, warnings):
            geometries[item_id] = container["geometry"]
            layout_parents[item_id] = container.get("parent")
            layout_kinds[item_id] = "container"

    for item_id, parent in parents.items():
        if parent is not None and parent not in container_ids:
            errors.append(f"container {item_id!r}: unknown parent {parent!r}")
        seen = {item_id}
        cursor = parent
        while cursor is not None:
            if cursor in seen:
                errors.append(f"container {item_id!r}: parent cycle detected")
                break
            seen.add(cursor)
            cursor = parents.get(cursor)

    for index, node in enumerate(nodes):
        context = f"nodes[{index}]"
        if not isinstance(node, dict):
            errors.append(f"{context}: must be an object")
            continue
        item_id = node.get("id")
        if not isinstance(item_id, str) or not item_id:
            errors.append(f"{context}: id is required")
            continue
        if item_id in ids:
            errors.append(f"{context}: duplicate id {item_id!r}")
        ids.add(item_id)
        node_ids.add(item_id)
        geometry_ok = check_shared_fields(node, context, errors, warnings)
        if not isinstance(node.get("service"), str) or not node["service"].strip():
            errors.append(f"{context}: service is required")
        container = node.get("container")
        if container is not None and container not in container_ids:
            errors.append(f"{context}: unknown container {container!r}")
        if geometry_ok:
            geometries[item_id] = node["geometry"]
            layout_parents[item_id] = container
            layout_kinds[item_id] = "node"
        if node.get("status") == "unresolved" and "要確認" not in node.get("label", ""):
            warnings.append(f"{context}: unresolved node label should include '要確認'")
        if len(node.get("label", "")) > 30:
            errors.append(f"{context}: label is too long for a card; keep it within 30 characters")
        if len(node.get("role", "")) > 32:
            errors.append(f"{context}: role is too long for a card; move details to architecture-notes.md")

    endpoint_ids = container_ids | node_ids
    for index, edge in enumerate(edges):
        context = f"edges[{index}]"
        if not isinstance(edge, dict):
            errors.append(f"{context}: must be an object")
            continue
        item_id = edge.get("id")
        if not isinstance(item_id, str) or not item_id:
            errors.append(f"{context}: id is required")
            continue
        if item_id in ids:
            errors.append(f"{context}: duplicate id {item_id!r}")
        ids.add(item_id)
        if edge.get("from") not in endpoint_ids:
            errors.append(f"{context}: unknown from endpoint {edge.get('from')!r}")
        if edge.get("to") not in endpoint_ids:
            errors.append(f"{context}: unknown to endpoint {edge.get('to')!r}")
        if edge.get("kind") not in EDGE_KINDS:
            errors.append(f"{context}: invalid edge kind")
        if edge.get("status") not in STATUSES:
            errors.append(f"{context}: invalid status")
        if not isinstance(edge.get("label"), str):
            errors.append(f"{context}: label must be a string")
        elif len(edge.get("label", "")) > 24:
            errors.append(f"{context}: edge label is too long; keep it within 24 characters or move it to notes")
        check_evidence(edge.get("evidence"), context, errors)
        if edge.get("status") == "unresolved" and "要確認" not in edge.get("label", ""):
            warnings.append(f"{context}: unresolved edge label should include '要確認'")

    if not nodes:
        warnings.append("nodes is empty")
    if nodes and not edges:
        warnings.append("edges is empty; confirm that the architecture truly has no important paths")

    check_icons(nodes, data.get("provider"), errors, warnings)
    if isinstance(canvas, dict) and canvas.get("width") and canvas.get("height"):
        check_labels(data, tokens, errors, warnings)

    canvas_width = canvas.get("width", 0) if isinstance(canvas, dict) else 0
    canvas_height = canvas.get("height", 0) if isinstance(canvas, dict) else 0
    for item_id, geometry in geometries.items():
        parent_id = layout_parents.get(item_id)
        if parent_id is None:
            limit_width, limit_height = canvas_width, canvas_height
            boundary = "canvas"
        else:
            parent_geometry = geometries.get(parent_id)
            if parent_geometry is None:
                continue
            limit_width, limit_height = parent_geometry["width"], parent_geometry["height"]
            boundary = f"parent {parent_id!r}"
        if geometry["x"] + geometry["width"] > limit_width or geometry["y"] + geometry["height"] > limit_height:
            errors.append(f"{layout_kinds[item_id]} {item_id!r} extends outside {boundary}")

    node_gap = float(tokens["geometry"]["node_gap"])
    siblings: dict[str | None, list[str]] = {}
    for item_id, parent_id in layout_parents.items():
        siblings.setdefault(parent_id, []).append(item_id)
    for parent_id, group in siblings.items():
        for index, first_id in enumerate(group):
            for second_id in group[index + 1 :]:
                first, second = geometries[first_id], geometries[second_id]
                if rectangles_overlap(first, second):
                    errors.append(
                        f"layout overlap under {parent_id or 'canvas'!r}: {first_id!r} and {second_id!r}"
                    )
                    continue
                gap = separation(first, second)
                if gap < node_gap - 0.5:
                    errors.append(
                        f"only {gap:.0f}px between {first_id!r} and {second_id!r} under "
                        f"{parent_id or 'canvas'!r}; keep siblings at least {node_gap:g}px apart"
                    )

    check_flow(data, geometries, layout_parents, warnings)

    legend = data.get("legend")
    legend_rect: dict[str, Any] | None = None
    if isinstance(legend, dict) and legend.get("show", True) and edges:
        used_edge_styles: list[str] = []
        for edge in edges:
            key = "unresolved" if edge.get("status") == "unresolved" else edge.get("kind")
            if key and key not in used_edge_styles:
                used_edge_styles.append(key)
        legend_rect = {
            "x": legend.get("x", tokens["geometry"]["outer_padding"]),
            "y": legend.get("y", canvas_height - 180),
            "width": max(220, legend.get("width", 240)),
            "height": 50 + len(used_edge_styles) * 30,
        }
        if legend_rect["x"] + legend_rect["width"] > canvas_width or legend_rect["y"] + legend_rect["height"] > canvas_height:
            errors.append("legend extends outside canvas")
        for item_id, geometry in geometries.items():
            if layout_parents[item_id] is None and rectangles_overlap(legend_rect, geometry):
                errors.append(f"legend overlaps top-level element {item_id!r}")

    if isinstance(canvas, dict) and canvas.get("width") and canvas.get("height"):
        check_padding(data, tokens, geometries, layout_parents, errors, warnings, legend_rect)

    if isinstance(data.get("title"), str) and len(data["title"]) > 50:
        warnings.append("title is longer than 50 characters; shorten it for scanability")
    if isinstance(data.get("subtitle"), str) and len(data["subtitle"]) > 70:
        warnings.append("subtitle is longer than 70 characters; move implementation details to notes")

    for field in ("omissions", "unresolved"):
        value = data.get(field)
        if not isinstance(value, list):
            errors.append(f"{field} must be an array")
            continue
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                errors.append(f"{field}[{index}] must be an object")
                continue
            for key in ("item", "reason"):
                if not isinstance(item.get(key), str) or not item[key].strip():
                    errors.append(f"{field}[{index}].{key} is required")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Terraform architecture diagram specification")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS)
    args = parser.parse_args()

    try:
        data = load_json(args.spec)
        tokens = load_json(args.tokens)
        data = layout_engine.resolve(data, tokens)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    errors, warnings = validate(data, tokens)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print(f"validation failed: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(f"validation passed: {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
