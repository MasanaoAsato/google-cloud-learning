#!/usr/bin/env python3

"""Build an editable Draw.io diagram from the intermediate specification.

Three choices here exist because of how the output gets read rather than how it
gets built:

- Boundary and card labels live in their own cells. A label attached directly to a
  container is drawn across the container's own border, which makes the top-level
  names the hardest text in the picture to read.
- Line breaks are computed by ``text_layout`` and emitted as ``nowrap`` blocks, so
  the browser cannot re-wrap Japanese text at an arbitrary character.
- Every resource, and every person or network drawn alongside it, gets a real
  Draw.io icon from the catalog. Lettered boxes defeat the point of a diagram.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import drawio_styles
import layout as layout_engine
import preview
import text_layout
from icon_catalog import IconCatalog
from validate_artifacts import validate_drawio
from validate_diagram_spec import load_json, validate

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = SKILL_DIR / "assets" / "base.drawio"
DEFAULT_TOKENS = SKILL_DIR / "assets" / "style-tokens.json"
DEFAULT_ICONS = SKILL_DIR / "assets" / "icon-styles.json"

EDGE_LABELS = {
    "traffic": "同期通信",
    "async": "非同期通信",
    "peer": "双方向・対等",
    "control": "制御・管理",
    "dependency": "構成上の依存",
    "special": "特殊経路",
}

def load_tokens(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read style tokens: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("style tokens root must be an object")
    return data


def graph_root(tree: ET.ElementTree) -> tuple[ET.Element, ET.Element]:
    model = tree.getroot().find("./diagram/mxGraphModel")
    if model is None:
        raise ValueError("base template has no mxGraphModel")
    root = model.find("root")
    if root is None:
        raise ValueError("base template has no graph root")
    return model, root


def evidence_attrs(item: dict[str, Any]) -> dict[str, str]:
    sources = []
    for evidence in item.get("evidence", []):
        source = evidence.get("source", "")
        line = evidence.get("line")
        if line:
            source = f"{source}:{line}"
        if source:
            sources.append(source)
    return {
        "evidenceStatus": item.get("status", ""),
        "evidenceSource": "; ".join(sources),
    }


def add_geometry(cell: ET.Element, geometry: dict[str, Any]) -> ET.Element:
    attrs = {
        "x": str(geometry.get("x", 0)),
        "y": str(geometry.get("y", 0)),
        "width": str(geometry.get("width", 0)),
        "height": str(geometry.get("height", 0)),
        "as": "geometry",
    }
    return ET.SubElement(cell, "mxGeometry", attrs)


def card_text_box(tokens: dict[str, Any], geometry: dict[str, Any]) -> tuple[float, float, float, float]:
    """Text area of a card: x, y, width, height, after icon and padding."""
    layout = tokens["geometry"]
    x = layout["card_padding_x"] + layout["icon_size"] + layout["card_icon_gap"]
    width = geometry["width"] - x - layout["card_padding_x"]
    y = layout["card_padding_y"]
    height = geometry["height"] - 2 * layout["card_padding_y"]
    return x, y, width, height


def node_label_html(
    item: dict[str, Any],
    tokens: dict[str, Any],
    width: float,
    show_address: bool,
) -> tuple[str, list[tuple[str, float, bool]]]:
    """Compose card label HTML with breaks chosen here, not by the browser."""
    typography = tokens["typography"]
    service_size = typography["service_size"]
    note_size = typography["note_size"]
    blocks: list[tuple[str, float, bool]] = []
    pieces: list[str] = []

    for line in text_layout.wrap(item["label"], width, service_size, bold=True):
        blocks.append((line, service_size, True))
        pieces.append(f'<div style="white-space:nowrap"><b>{html.escape(line)}</b></div>')

    role = (item.get("role") or "").strip()
    if role:
        for line in text_layout.wrap(role, width, note_size):
            blocks.append((line, note_size, False))
            pieces.append(
                '<div style="white-space:nowrap">'
                f'<span style="font-size:{note_size:g}px;color:{typography["muted_text_color"]}">'
                f"{html.escape(line)}</span></div>"
            )

    address = (item.get("terraform_address") or "").strip()
    if address and show_address:
        for line in text_layout.wrap(address, width, typography["address_size"]):
            blocks.append((line, typography["address_size"], False))
            pieces.append(
                '<div style="white-space:nowrap">'
                f'<span style="font-size:{typography["address_size"]:g}px;'
                f'color:{typography["muted_text_color"]}">{html.escape(line)}</span></div>'
            )

    if item.get("status") == "unresolved":
        blocks.append(("要確認", note_size, True))
        pieces.append(
            '<div style="white-space:nowrap">'
            f'<span style="font-size:{note_size:g}px;color:#F29900"><b>要確認</b></span></div>'
        )
    return "".join(pieces), blocks


def blocks_height(blocks: list[tuple[str, float, bool]]) -> float:
    return sum(text_layout.line_height(size) for _, size, _ in blocks)


def add_canvas_background(
    root: ET.Element,
    spec: dict[str, Any],
    tokens: dict[str, Any],
) -> None:
    """Keep the configured canvas margin when Draw.io crops an export.

    Draw.io normally exports the bounding box of visible cells, which removes the
    whitespace reserved by the canvas layout. A white, locked cell covering the
    full canvas makes that intended area part of the bounds and also gives raster
    and SVG exports an explicit white background.
    """
    background = str(tokens.get("canvas", {}).get("background", "#FFFFFF"))
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": "meta-canvas-background",
            "value": "",
            "style": (
                "rounded=0;whiteSpace=wrap;html=1;"
                f"fillColor={background};strokeColor=none;strokeWidth=0;"
                "opacity=100;locked=1;movable=0;resizable=0;rotatable=0;"
                "deletable=0;editable=0;connectable=0;pointerEvents=0;"
            ),
            "vertex": "1",
            "parent": "layer-background",
            "dataKind": "canvas-background",
            "exportBounds": "canvas",
        },
    )
    add_geometry(
        cell,
        {
            "x": 0,
            "y": 0,
            "width": spec["canvas"]["width"],
            "height": spec["canvas"]["height"],
        },
    )


def add_title(root: ET.Element, spec: dict[str, Any], tokens: dict[str, Any]) -> None:
    typography = tokens["typography"]
    layout = tokens["geometry"]
    width = spec["canvas"]["width"] - 2 * layout["outer_padding"]
    title = ET.SubElement(
        root,
        "mxCell",
        {
            "id": "meta-title",
            "value": html.escape(spec["title"]),
            "style": drawio_styles.text_style(tokens, typography["title_size"], bold=True),
            "vertex": "1",
            "parent": "layer-labels",
            "dataKind": "title",
        },
    )
    add_geometry(title, {"x": layout["outer_padding"], "y": 20, "width": width, "height": 30})
    subtitle_value = spec.get("subtitle", "").strip()
    if subtitle_value:
        subtitle = ET.SubElement(
            root,
            "mxCell",
            {
                "id": "meta-subtitle",
                "value": html.escape(subtitle_value),
                "style": drawio_styles.text_style(
                    tokens, typography["note_size"], color=typography["muted_text_color"]
                ),
                "vertex": "1",
                "parent": "layer-labels",
                "dataKind": "subtitle",
            },
        )
        add_geometry(
            subtitle, {"x": layout["outer_padding"], "y": 52, "width": width, "height": 20}
        )


def container_depth(item: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> int:
    depth = 0
    parent = item.get("parent")
    seen: set[str] = set()
    while parent and parent not in seen:
        seen.add(parent)
        depth += 1
        parent = by_id.get(parent, {}).get("parent")
    return depth


def add_containers(root: ET.Element, spec: dict[str, Any], tokens: dict[str, Any]) -> None:
    typography = tokens["typography"]
    layout = tokens["geometry"]
    by_id = {item["id"]: item for item in spec["containers"]}
    for item in sorted(spec["containers"], key=lambda value: container_depth(value, by_id)):
        attrs = {
            "id": item["id"],
            "value": "",
            "style": drawio_styles.container_style(tokens, item),
            "vertex": "1",
            "parent": item.get("parent") or "layer-boundaries",
            "dataKind": "container",
            "provider": item.get("provider", "neutral"),
            "containerKind": item.get("kind", "group"),
            "boundaryLabel": item["label"],
            **evidence_attrs(item),
        }
        cell = ET.SubElement(root, "mxCell", attrs)
        add_geometry(cell, item["geometry"])

        size = (
            typography["boundary_size"]
            if item.get("kind") in drawio_styles.BOUNDARY_KINDS
            else typography["sub_boundary_size"]
        )
        # grIcon付きの境界（AWS Groups）は左上角にアイコンが描かれるため、
        # 境界名をその右へ逃がして重なりを避ける。
        indent = drawio_styles.container_label_indent(attrs["style"])
        inset = layout["label_inset"] + indent
        available = item["geometry"]["width"] - inset - layout["label_inset"]
        lines = text_layout.wrap(item["label"], available, size, bold=True)
        height = max(20.0, len(lines) * text_layout.line_height(size))
        label = ET.SubElement(
            root,
            "mxCell",
            {
                "id": f"{item['id']}__label",
                # The label is its own cell so it sits inside the frame instead of
                # being painted across the boundary line.
                "value": text_layout.html_lines(lines, html.escape),
                "style": drawio_styles.text_style(
                    tokens,
                    size,
                    bold=True,
                    vertical="top",
                    color=drawio_styles.container_label_color(tokens, item),
                ),
                "vertex": "1",
                "parent": item["id"],
                "dataKind": "container-label",
            },
        )
        add_geometry(label, {"x": inset, "y": 12, "width": available, "height": height})


def add_nodes(
    root: ET.Element,
    spec: dict[str, Any],
    tokens: dict[str, Any],
    catalog: IconCatalog,
) -> None:
    layout = tokens["geometry"]
    show_all_addresses = bool(spec.get("show_terraform_addresses", False))
    diagram_provider = spec.get("provider")
    for item in spec["nodes"]:
        show_address = show_all_addresses or bool(item.get("show_terraform_address", False))
        attrs = {
            "id": item["id"],
            "value": "",
            "style": drawio_styles.card_style(tokens, item),
            "vertex": "1",
            "parent": item.get("container") or "layer-resources",
            "dataKind": "node",
            "provider": item.get("provider", "neutral"),
            "service": item.get("service", ""),
            **evidence_attrs(item),
        }
        if item.get("terraform_address"):
            attrs["terraformAddress"] = item["terraform_address"]
        cell = ET.SubElement(root, "mxCell", attrs)
        add_geometry(cell, item["geometry"])

        custom = (item.get("shape_style") or "").strip()
        if custom:
            icon_style, icon_source = custom.rstrip(";") + ";", "spec shape_style"
        else:
            # A neutral subject belongs to the diagram's cloud for icon purposes, so a
            # GCP figure draws its people with the Google Cloud icon family.
            provider = item.get("provider")
            if provider not in {"aws", "azure", "gcp"}:
                provider = diagram_provider
            service = item.get("service", "")
            try:
                icon_style, icon_source = catalog.resolve(service, provider)
            except KeyError:
                # Last tier of the icon policy: a plain box with the service name.
                icon_style = drawio_styles.placeholder_icon_style()
                icon_source = f"placeholder: no Draw.io icon for {service!r}"
                print(
                    f"WARNING: node {item['id']!r}: no Draw.io icon for {service!r}; "
                    "drew a plain box instead. Fetch one with maintenance/"
                    "sync_sidebar_icons.py or record the fallback in architecture-notes.md."
                )
        icon_size = layout["icon_size"]
        icon = ET.SubElement(
            root,
            "mxCell",
            {
                "id": f"{item['id']}__icon",
                "value": "",
                "style": icon_style,
                "vertex": "1",
                "parent": item["id"],
                "dataKind": "node-icon",
                "iconSource": icon_source,
            },
        )
        add_geometry(
            icon,
            {
                "x": layout["card_padding_x"],
                "y": round((item["geometry"]["height"] - icon_size) / 2, 1),
                "width": icon_size,
                "height": icon_size,
            },
        )

        box_x, box_y, box_width, box_height = card_text_box(tokens, item["geometry"])
        label_html, blocks = node_label_html(item, tokens, box_width, show_address)
        used = blocks_height(blocks)
        if used > box_height + 0.5:
            raise ValueError(
                f"node {item['id']!r}: label and role need {used:.0f}px of text height but the "
                f"card only offers {box_height:.0f}px. Make the card taller or wider, or move "
                "detail to architecture-notes.md."
            )
        label = ET.SubElement(
            root,
            "mxCell",
            {
                "id": f"{item['id']}__label",
                "value": label_html,
                "style": drawio_styles.text_style(tokens, tokens["typography"]["service_size"]),
                "vertex": "1",
                "parent": item["id"],
                "dataKind": "node-label",
            },
        )
        add_geometry(
            label, {"x": box_x, "y": box_y, "width": box_width, "height": box_height}
        )


def add_edges(root: ET.Element, spec: dict[str, Any], tokens: dict[str, Any]) -> None:
    provider = spec.get("provider")
    for item in spec["edges"]:
        label = item.get("label", "")
        if item.get("status") == "unresolved" and "要確認" not in label:
            label = f"{label}（要確認）" if label else "要確認"
        cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": item["id"],
                "value": html.escape(label),
                "style": drawio_styles.edge_style(tokens, item, provider),
                "edge": "1",
                "parent": "layer-flows",
                "source": item["from"],
                "target": item["to"],
                "dataKind": "edge",
                "edgeKind": item.get("kind", "dependency"),
                **evidence_attrs(item),
            },
        )
        geometry = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
        waypoints = item.get("waypoints", [])
        if waypoints:
            points = ET.SubElement(geometry, "Array", {"as": "points"})
            for point in waypoints:
                ET.SubElement(points, "mxPoint", {"x": str(point["x"]), "y": str(point["y"])})


def legend_size(spec: dict[str, Any], tokens: dict[str, Any]) -> tuple[list[str], float, float]:
    used: list[str] = []
    for item in spec["edges"]:
        key = "unresolved" if item.get("status") == "unresolved" else item.get("kind")
        if key and key not in used:
            used.append(key)
    legend_spec = spec.get("legend") or {}
    width = max(220.0, float(legend_spec.get("width", 240)))
    height = 50 + len(used) * 30
    return used, width, height


def add_legend(root: ET.Element, spec: dict[str, Any], tokens: dict[str, Any]) -> None:
    typography = tokens["typography"]
    layout = tokens["geometry"]
    used, width, height = legend_size(spec, tokens)
    legend_spec = spec.get("legend") or {
        "show": True,
        "x": layout["outer_padding"],
        "y": spec["canvas"]["height"] - height - layout["outer_padding"],
    }
    if not legend_spec.get("show", True) or not used:
        return

    margin = layout["outer_padding"]
    x = max(margin, min(float(legend_spec.get("x", margin)), spec["canvas"]["width"] - width - margin))
    y = max(margin, min(float(legend_spec.get("y", margin)), spec["canvas"]["height"] - height - margin))
    legend = ET.SubElement(
        root,
        "mxCell",
        {
            "id": "meta-legend",
            "value": "",
            "style": (
                "container=1;collapsible=0;rounded=0;whiteSpace=wrap;html=1;"
                "fillColor=#FFFFFF;strokeColor=#BDC1C6;strokeWidth=1.5;sketch=0;"
            ),
            "vertex": "1",
            "parent": "layer-legend",
            "dataKind": "legend",
        },
    )
    add_geometry(legend, {"x": x, "y": y, "width": width, "height": height})

    heading = ET.SubElement(
        root,
        "mxCell",
        {
            "id": "meta-legend-title",
            "value": "凡例",
            "style": drawio_styles.text_style(tokens, typography["service_size"], bold=True, vertical="top"),
            "vertex": "1",
            "parent": "meta-legend",
            "dataKind": "legend-title",
        },
    )
    add_geometry(heading, {"x": 14, "y": 10, "width": width - 28, "height": 20})

    provider = spec.get("provider")
    for index, key in enumerate(used):
        row = 40 + index * 30
        token = drawio_styles.edge_token(
            tokens, {"kind": key, "status": "unresolved" if key == "unresolved" else "confirmed"}, provider
        )
        line_style = (
            "shape=line;html=1;sketch=0;"
            f"strokeColor={token['stroke']};strokeWidth={token['width']};"
            f"dashed={1 if token['dashed'] else 0};endArrow={token['arrow']};endFill=1;"
        )
        if token.get("dashed") and token.get("dash_pattern"):
            line_style += f"dashPattern={token['dash_pattern']};"
        if token.get("start_arrow"):
            line_style += f"startArrow={token['start_arrow']};startFill=1;"
        line = ET.SubElement(
            root,
            "mxCell",
            {
                "id": f"meta-legend-line-{index}",
                "value": "",
                "style": line_style,
                "vertex": "1",
                "parent": "meta-legend",
                "dataKind": "legend-line",
            },
        )
        add_geometry(line, {"x": 14, "y": row, "width": 48, "height": 10})
        label = "要確認" if key == "unresolved" else EDGE_LABELS.get(key, key)
        text = ET.SubElement(
            root,
            "mxCell",
            {
                "id": f"meta-legend-label-{index}",
                "value": html.escape(label),
                "style": drawio_styles.text_style(tokens, typography["note_size"]),
                "vertex": "1",
                "parent": "meta-legend",
                "dataKind": "legend-label",
            },
        )
        add_geometry(text, {"x": 74, "y": row - 5, "width": width - 88, "height": 20})


def build(
    spec: dict[str, Any],
    tokens: dict[str, Any],
    template: Path,
    catalog: IconCatalog,
) -> ET.ElementTree:
    try:
        tree = ET.parse(template)
    except (OSError, ET.ParseError) as exc:
        raise ValueError(f"cannot read base template: {exc}") from exc
    model, root = graph_root(tree)
    model.set("pageWidth", str(spec["canvas"]["width"]))
    model.set("pageHeight", str(spec["canvas"]["height"]))
    model.set("dx", str(spec["canvas"]["width"]))
    model.set("dy", str(spec["canvas"]["height"]))
    model.set("background", str(tokens.get("canvas", {}).get("background", "#FFFFFF")))

    existing_ids = {cell.attrib.get("id") for cell in root if cell.tag == "mxCell"}
    required_layers = {
        "0",
        "layer-background",
        "layer-boundaries",
        "layer-resources",
        "layer-flows",
        "layer-labels",
        "layer-legend",
    }
    if not required_layers.issubset(existing_ids):
        raise ValueError("base template is missing one or more required layers")

    add_canvas_background(root, spec, tokens)
    add_title(root, spec, tokens)
    add_containers(root, spec, tokens)
    add_nodes(root, spec, tokens, catalog)
    add_edges(root, spec, tokens)
    add_legend(root, spec, tokens)
    return tree


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a diagram specification, build the .drawio, and render a preview"
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--preview",
        type=Path,
        help="also render a layout preview PNG here so the result can be looked at",
    )
    parser.add_argument("--preview-width", type=int, default=1800)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS)
    parser.add_argument("--icons", type=Path, default=DEFAULT_ICONS)
    parser.add_argument(
        "--resolved-spec",
        type=Path,
        help="also write the spec with computed geometry here, for hand-tuning single items",
    )
    args = parser.parse_args()

    try:
        spec = load_json(args.spec)
        tokens = load_tokens(args.tokens)
        # Fill in geometry for items that declare only grid cells. Specs with
        # full hand-placed geometry pass through unchanged.
        spec = layout_engine.resolve(spec, tokens)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.resolved_spec:
        args.resolved_spec.parent.mkdir(parents=True, exist_ok=True)
        args.resolved_spec.write_text(
            json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {args.resolved_spec}")

    spec_errors, spec_warnings = validate(spec, tokens)
    for warning in spec_warnings:
        print(f"WARNING: {warning}")
    if spec_errors:
        for error in spec_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    try:
        catalog = IconCatalog.load(args.icons)
        tree = build(spec, tokens, args.template, catalog)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(tree, space="  ")
        tree.write(args.output, encoding="utf-8", xml_declaration=True)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {args.output}")

    # Check the file that was just written, so one command covers the whole build.
    artifact_errors, artifact_warnings, inventory = validate_drawio(spec, args.output)
    for warning in artifact_warnings:
        print(f"WARNING: {warning}")
    if artifact_errors:
        for error in artifact_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"checks passed: {inventory.get('vertex_count', 0)} vertices, "
        f"{inventory.get('edge_count', 0)} edges"
    )

    if args.preview:
        try:
            print(f"wrote {preview.write_preview(args.output, args.preview, tokens, args.preview_width)}")
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            print(f"ERROR: cannot render preview: {exc}", file=sys.stderr)
            return 1
        print("look at the preview before treating the diagram as finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
