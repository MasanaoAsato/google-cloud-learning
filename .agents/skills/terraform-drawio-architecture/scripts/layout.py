#!/usr/bin/env python3

"""Compute pixel geometry for a diagram spec that declares only structure.

The intermediate spec used to require hand-computed absolute coordinates for
every container and node, and the validator then rejected anything that broke
the spacing contract. That turned authoring into trial-and-error constraint
solving. This module removes that loop: an item may omit ``geometry`` and
declare only its cell in the parent's grid (``grid: {"row": R, "col": C}``);
sizes and positions are derived here so the spacing contract holds by
construction.

Explicit ``geometry`` is always respected untouched, both per item and for the
whole spec: a fully hand-placed spec passes through byte-identical, and a
pinned item inside an auto-laid parent keeps its coordinates. Quality tuning by
hand therefore stays possible everywhere.

Alignment rule: all members of a grid column share the column's width slot and
are centered in it, so vertical edges between rows run straight without
waypoints.
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

import drawio_styles
import text_layout

TITLE_BAND = 90.0  # keep clear of the title block, mirrored in validate_diagram_spec
GRID = 10.0


def snap_up(value: float) -> int:
    return int(math.ceil(value / GRID - 1e-9) * GRID)


def snap_down(value: float) -> int:
    return int(math.floor(value / GRID + 1e-9) * GRID)


def _has_geometry(item: dict[str, Any]) -> bool:
    return isinstance(item.get("geometry"), dict)


def _grid_cell(item: dict[str, Any], context: str, fallback_row: int) -> tuple[int, int]:
    grid = item.get("grid")
    if grid is None:
        return fallback_row, 0
    if not isinstance(grid, dict):
        raise ValueError(f"{context}: grid must be an object like {{\"row\": 0, \"col\": 0}}")
    row, col = grid.get("row"), grid.get("col", 0)
    for name, value in (("row", row), ("col", col)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{context}: grid.{name} must be a non-negative integer")
    return row, col


def node_size(node: dict[str, Any], tokens: dict[str, Any]) -> tuple[float, float]:
    """Card size derived from the same wrapping the builder will use."""
    layout = tokens["geometry"]
    typography = tokens["typography"]
    width = int(layout["card_width"])
    text_width = width - 2 * layout["card_padding_x"] - layout["icon_size"] - layout["card_icon_gap"]
    used = 0.0
    for value, size, bold in (
        (node.get("label", ""), typography["service_size"], True),
        (node.get("role") or "", typography["note_size"], False),
    ):
        if value:
            lines = text_layout.wrap(value, text_width, size, bold=bold)
            used += len(lines) * text_layout.line_height(size)
    if node.get("status") == "unresolved":
        used += text_layout.line_height(typography["note_size"])
    height = max(
        float(layout["card_height"]),
        snap_up(used + 2 * layout["card_padding_y"]),
        snap_up(layout["icon_size"] + 2 * layout["card_padding_y"]),
    )
    return width, height


def container_min_width(container: dict[str, Any], tokens: dict[str, Any]) -> float:
    """Wide enough that the boundary name fits on one line inside the header band."""
    layout = tokens["geometry"]
    typography = tokens["typography"]
    size = (
        typography["boundary_size"]
        if container.get("kind") in drawio_styles.BOUNDARY_KINDS
        else typography["sub_boundary_size"]
    )
    style = drawio_styles.container_style(tokens, container)
    indent = drawio_styles.container_label_indent(style)
    needed = text_layout.measure(container.get("label", ""), size, bold=True)
    return snap_up(needed + 2 * layout["label_inset"] + indent + 4)


class _Frame:
    """Placement work for the children of one parent (a container or the canvas)."""

    def __init__(self, origin_x: float, origin_y: float, gap: float) -> None:
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.gap = gap
        self.flow: list[tuple[int, int, dict[str, Any], float, float]] = []
        self.pinned: list[dict[str, Any]] = []

    def place(self, context_of) -> tuple[float, float]:
        """Assign geometry to flow items; return the content extent (w, h)."""
        cells: dict[tuple[int, int], dict[str, Any]] = {}
        for row, col, item, _, _ in self.flow:
            other = cells.get((row, col))
            if other is not None:
                raise ValueError(
                    f"{context_of(item)} and {context_of(other)} both occupy grid cell "
                    f"(row {row}, col {col}) under the same parent; give them different cells"
                )
            cells[(row, col)] = item

        rows = sorted({row for row, _, _, _, _ in self.flow})
        cols = sorted({col for _, col, _, _, _ in self.flow})
        row_height = {row: 0.0 for row in rows}
        col_width = {col: 0.0 for col in cols}
        for row, col, _, width, height in self.flow:
            row_height[row] = max(row_height[row], height)
            col_width[col] = max(col_width[col], width)

        col_x: dict[int, float] = {}
        cursor = self.origin_x
        for col in cols:
            col_x[col] = cursor
            cursor += col_width[col] + self.gap
        row_y: dict[int, float] = {}
        cursor = self.origin_y
        for row in rows:
            row_y[row] = cursor
            cursor += row_height[row] + self.gap

        for row, col, item, width, height in self.flow:
            item["geometry"] = {
                "x": int(col_x[col]) + snap_down((col_width[col] - width) / 2),
                "y": int(row_y[row]) + snap_down((row_height[row] - height) / 2),
                "width": int(width),
                "height": int(height),
            }

        right = self.origin_x
        bottom = self.origin_y
        if self.flow:
            right = max(col_x[col] + col_width[col] for col in cols)
            bottom = max(row_y[row] + row_height[row] for row in rows)
        for item in self.pinned:
            geometry = item["geometry"]
            right = max(right, geometry["x"] + geometry["width"])
            bottom = max(bottom, geometry["y"] + geometry["height"])
        return right - self.origin_x, bottom - self.origin_y


def _layout_children(
    parent: dict[str, Any] | None,
    children: list[dict[str, Any]],
    tokens: dict[str, Any],
    sizes: dict[str, tuple[float, float]],
    pinned_ids: set[str],
    flow: str,
    context_of,
) -> tuple[float, float]:
    layout = tokens["geometry"]
    if parent is None:
        origin = (float(layout["outer_padding"]), TITLE_BAND)
    else:
        origin = (float(layout["container_padding"]), float(layout["container_header"]))
    frame = _Frame(origin[0], origin[1], float(layout["node_gap"]))

    # Items without a grid cell continue along the declared flow direction, so
    # a lazily written spec still reads left to right (or top to bottom).
    axis = 0 if flow == "vertical" else 1
    fallback = 1 + max(
        (_grid_cell(item, context_of(item), 0)[axis] for item in children if item.get("grid") is not None),
        default=-1,
    )
    for item in children:
        if item.get("id") in pinned_ids:
            frame.pinned.append(item)
            continue
        if item.get("grid") is None:
            row, col = (fallback, 0) if flow == "vertical" else (0, fallback)
            fallback += 1
        else:
            row, col = _grid_cell(item, context_of(item), 0)
        width, height = sizes[item["id"]]
        frame.flow.append((row, col, item, width, height))
    return frame.place(context_of)


def _legend_height(spec: dict[str, Any]) -> float:
    used: list[str] = []
    for edge in spec.get("edges", []):
        key = "unresolved" if edge.get("status") == "unresolved" else edge.get("kind")
        if key and key not in used:
            used.append(key)
    return 50.0 + len(used) * 30.0 if used else 0.0


def resolve(spec: dict[str, Any], tokens: dict[str, Any]) -> dict[str, Any]:
    """Return a spec whose every item has geometry and whose canvas is set.

    A spec that already carries full geometry and a canvas is returned as-is,
    so hand-tuned diagrams are never rewritten.
    """
    containers = spec.get("containers", [])
    nodes = spec.get("nodes", [])
    if not isinstance(containers, list) or not isinstance(nodes, list):
        return spec
    items = [item for item in containers + nodes if isinstance(item, dict)]
    if all(_has_geometry(item) for item in items) and isinstance(spec.get("canvas"), dict):
        return spec

    spec = deepcopy(spec)
    containers = [item for item in spec.get("containers", []) if isinstance(item, dict)]
    nodes = [item for item in spec.get("nodes", []) if isinstance(item, dict)]
    layout = tokens["geometry"]
    flow = spec.get("flow") if spec.get("flow") in ("horizontal", "vertical") else "horizontal"
    # Geometry written by this resolver must not be mistaken for a hand-pinned
    # position, so remember which items the author actually pinned.
    pinned_ids = {item.get("id") for item in containers + nodes if _has_geometry(item)}

    contexts: dict[str, str] = {}
    for index, item in enumerate(containers):
        contexts[item.get("id", f"containers[{index}]")] = f"containers[{index}] ({item.get('id')})"
    for index, item in enumerate(nodes):
        contexts[item.get("id", f"nodes[{index}]")] = f"nodes[{index}] ({item.get('id')})"

    def context_of(item: dict[str, Any]) -> str:
        return contexts.get(item.get("id", ""), repr(item.get("id")))

    children: dict[str | None, list[dict[str, Any]]] = {}
    for item in containers:
        children.setdefault(item.get("parent"), []).append(item)
    for item in nodes:
        children.setdefault(item.get("container"), []).append(item)

    sizes: dict[str, tuple[float, float]] = {}
    for node in nodes:
        if _has_geometry(node):
            sizes[node["id"]] = (node["geometry"]["width"], node["geometry"]["height"])
        else:
            sizes[node["id"]] = node_size(node, tokens)

    def size_container(container: dict[str, Any]) -> tuple[float, float]:
        own = children.get(container.get("id"), [])
        for child in own:
            if child in containers and child["id"] not in sizes:
                sizes[child["id"]] = size_container(child)
        if container.get("id") in pinned_ids:
            width, height = container["geometry"]["width"], container["geometry"]["height"]
            if any(child.get("id") not in pinned_ids for child in own):
                content_w, content_h = _layout_children(
                    container, own, tokens, sizes, pinned_ids, flow, context_of
                )
                needed_w = content_w + 2 * layout["container_padding"]
                needed_h = content_h + layout["container_header"] + layout["container_padding"]
                if needed_w > width + 0.5 or needed_h > height + 0.5:
                    raise ValueError(
                        f"{context_of(container)}: pinned at {width:g}x{height:g}px but its "
                        f"auto-laid children need {needed_w:g}x{needed_h:g}px. Enlarge it or "
                        "remove its geometry to let the layout size it"
                    )
        else:
            content_w, content_h = _layout_children(
                container, own, tokens, sizes, pinned_ids, flow, context_of
            )
            width = max(
                snap_up(content_w + 2 * layout["container_padding"]),
                container_min_width(container, tokens),
            )
            height = snap_up(content_h + layout["container_header"] + layout["container_padding"])
        sizes[container["id"]] = (width, height)
        return width, height

    for container in children.get(None, []):
        if container in containers and container["id"] not in sizes:
            size_container(container)
    for container in containers:  # containers whose parent id is dangling still get sized
        if container["id"] not in sizes:
            size_container(container)

    top = children.get(None, [])
    content_w, content_h = _layout_children(None, top, tokens, sizes, pinned_ids, flow, context_of)

    outer = float(layout["outer_padding"])
    gap = float(layout["node_gap"])
    legend_h = 0.0
    if spec.get("legend") is None and spec.get("edges"):
        legend_h = _legend_height(spec)

    width = snap_up(content_w + 2 * outer)
    height = snap_up(TITLE_BAND + content_h + outer + (gap + legend_h if legend_h else 0))

    canvas = spec.get("canvas")
    if isinstance(canvas, dict):
        width = max(width, float(canvas.get("width", 0)))
        height = max(height, float(canvas.get("height", 0)))
    spec["canvas"] = {"width": int(width), "height": int(height)}

    if legend_h:
        spec["legend"] = {
            "show": True,
            "x": int(outer),
            "y": snap_up(TITLE_BAND + content_h + gap),
        }
    return spec
