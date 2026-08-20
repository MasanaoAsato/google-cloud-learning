#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import html
import json
import sys
import urllib.parse
import zlib
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def decode_diagram_text(text: str) -> ET.Element:
    encoded = urllib.parse.unquote(text.strip())
    encoded += "=" * (-len(encoded) % 4)
    try:
        compressed = base64.b64decode(encoded)
        inflated = zlib.decompress(compressed, -15).decode("utf-8")
        xml = urllib.parse.unquote(inflated)
        return ET.fromstring(xml)
    except (ValueError, zlib.error, UnicodeDecodeError, ET.ParseError) as exc:
        raise ValueError(f"cannot decode compressed draw.io diagram: {exc}") from exc


def read_mxfile(path: Path) -> ET.Element:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ValueError(f"cannot parse XML: {exc}") from exc

    name = local_name(root.tag)
    if name == "mxfile":
        return root
    if name != "svg":
        raise ValueError(f"unsupported root element: {name}")

    embedded = root.attrib.get("content")
    if not embedded:
        raise ValueError("SVG does not contain embedded draw.io XML in the content attribute")
    try:
        mxfile = ET.fromstring(embedded)
    except ET.ParseError:
        try:
            mxfile = ET.fromstring(html.unescape(embedded))
        except ET.ParseError as exc:
            raise ValueError(f"embedded draw.io XML is invalid: {exc}") from exc
    if local_name(mxfile.tag) != "mxfile":
        raise ValueError("SVG content attribute does not contain an mxfile")
    return mxfile


def read_graph_model(mxfile: ET.Element) -> ET.Element:
    diagram = next((element for element in mxfile if local_name(element.tag) == "diagram"), None)
    if diagram is None:
        raise ValueError("mxfile has no diagram")

    child = next((element for element in diagram if local_name(element.tag) == "mxGraphModel"), None)
    if child is not None:
        return child

    text = (diagram.text or "").strip()
    if not text:
        raise ValueError("diagram has neither mxGraphModel nor compressed content")
    model = decode_diagram_text(text)
    if local_name(model.tag) != "mxGraphModel":
        raise ValueError("decoded diagram is not an mxGraphModel")
    return model


def geometry_of(cell: ET.Element) -> dict[str, Any] | None:
    geometry = next((child for child in cell if local_name(child.tag) == "mxGeometry"), None)
    if geometry is None:
        return None
    result: dict[str, Any] = {}
    for key in ("x", "y", "width", "height", "relative"):
        if key not in geometry.attrib:
            continue
        raw = geometry.attrib[key]
        if key == "relative":
            result[key] = raw == "1"
            continue
        try:
            result[key] = float(raw)
        except ValueError:
            result[key] = raw
    return result


def waypoints_of(cell: ET.Element) -> list[dict[str, float]]:
    geometry = next((child for child in cell if local_name(child.tag) == "mxGeometry"), None)
    if geometry is None:
        return []
    points: list[dict[str, float]] = []
    for array in geometry:
        if local_name(array.tag) != "Array" or array.attrib.get("as") != "points":
            continue
        for point in array:
            if local_name(point.tag) != "mxPoint":
                continue
            try:
                points.append({"x": float(point.attrib["x"]), "y": float(point.attrib["y"])})
            except (KeyError, ValueError):
                continue
    return points


def graph_inventory(model: ET.Element) -> dict[str, Any]:
    cells: list[dict[str, Any]] = []
    for cell in model.iter():
        if local_name(cell.tag) != "mxCell":
            continue
        item = {
            "id": cell.attrib.get("id"),
            "value": cell.attrib.get("value", ""),
            "parent": cell.attrib.get("parent"),
            "source": cell.attrib.get("source"),
            "target": cell.attrib.get("target"),
            "vertex": cell.attrib.get("vertex") == "1",
            "edge": cell.attrib.get("edge") == "1",
            "style": cell.attrib.get("style", ""),
            "data_kind": cell.attrib.get("dataKind"),
            "edge_kind": cell.attrib.get("edgeKind"),
            "terraform_address": cell.attrib.get("terraformAddress"),
            "evidence_status": cell.attrib.get("evidenceStatus"),
            "evidence_source": cell.attrib.get("evidenceSource"),
            "geometry": geometry_of(cell),
            "waypoints": waypoints_of(cell),
        }
        cells.append(item)

    vertices = [cell for cell in cells if cell["vertex"]]
    edges = [cell for cell in cells if cell["edge"]]
    return {
        "cell_count": len(cells),
        "vertex_count": len(vertices),
        "edge_count": len(edges),
        "cells": cells,
    }


def write_uncompressed_mxfile(mxfile: ET.Element, path: Path) -> None:
    for diagram in mxfile:
        if local_name(diagram.tag) != "diagram":
            continue
        if any(local_name(child.tag) == "mxGraphModel" for child in diagram):
            continue
        text = (diagram.text or "").strip()
        if not text:
            continue
        model = decode_diagram_text(text)
        diagram.text = None
        diagram.append(model)
    ET.indent(mxfile, space="  ")
    ET.ElementTree(mxfile).write(path, encoding="utf-8", xml_declaration=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect draw.io XML or a Draw.io-exported SVG")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, help="Write inventory JSON instead of stdout")
    parser.add_argument("--extract-drawio", type=Path, help="Write an uncompressed .drawio file")
    args = parser.parse_args()

    try:
        mxfile = read_mxfile(args.input)
        model = read_graph_model(mxfile)
        inventory = graph_inventory(model)
        if args.extract_drawio:
            write_uncompressed_mxfile(mxfile, args.extract_drawio)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(inventory, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
