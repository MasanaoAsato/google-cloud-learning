#!/usr/bin/env python3

"""Render a preview PNG from a ``.drawio`` so layout breakage is visible at once.

Automated checks catch overlaps and missing evidence. They cannot tell you that a
boundary name sits on its own border, that a card is too small for its text, or
that a frame is mostly empty. This renderer draws the same coordinates and the
same pre-computed label lines the builder wrote, locally and in about a second, so
those defects surface before anyone else sees the diagram.

Draw.io's built-in stencils cannot be rasterised outside the app, so they appear as
a light placeholder — position and size are still checkable. Open the ``.drawio``
in the VS Code Draw.io extension to see the real icons. This output is a layout
proof, never the artifact.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import quoteattr

import text_layout
from inspect_drawio import graph_inventory, read_graph_model, read_mxfile

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TOKENS = SKILL_DIR / "assets" / "style-tokens.json"
FONT = "Noto Sans JP,Hiragino Sans,Arial,sans-serif"
DIV_RE = re.compile(r"<div[^>]*>(.*?)</div>", re.S)
SIZE_RE = re.compile(r"font-size:\s*([0-9.]+)")
COLOR_RE = re.compile(r"color:\s*(#[0-9A-Fa-f]{3,8})")
TAG_RE = re.compile(r"<[^>]+>")


def parse_style(style: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in style.split(";"):
        if not part:
            continue
        key, _, value = part.partition("=")
        result[key.strip()] = value.strip() or "1"
    return result


class Line:
    """One rendered line of a label, with the font it should be drawn in."""

    def __init__(self, text: str, size: float, bold: bool, color: str) -> None:
        self.text = text
        self.size = size
        self.bold = bold
        self.color = color


def label_lines(value: str, style: dict[str, str]) -> list[Line]:
    """Read back the lines the builder fixed into the label HTML."""
    if not value:
        return []
    base_size = float(style.get("fontSize", 12))
    base_bold = style.get("fontStyle") in {"1", "3"}
    base_color = style.get("fontColor", "#202124")

    blocks = DIV_RE.findall(value) or [value]
    lines: list[Line] = []
    for block in blocks:
        size_match = SIZE_RE.search(block)
        color_match = COLOR_RE.search(block)
        size = float(size_match.group(1)) if size_match else base_size
        color = color_match.group(1) if color_match else base_color
        bold = base_bold or "<b>" in block
        text = html.unescape(TAG_RE.sub("", block)).strip()
        if text:
            lines.append(Line(text, size, bold, color))
    return lines


def absolute(cell: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> tuple[float, ...] | None:
    geometry = cell.get("geometry") or {}
    if "width" not in geometry:
        return None
    x, y = float(geometry.get("x", 0)), float(geometry.get("y", 0))
    parent, seen = cell.get("parent"), {cell.get("id")}
    while parent in by_id and parent not in seen:
        seen.add(parent)
        box = by_id[parent].get("geometry") or {}
        if "width" not in box:
            break
        x += float(box.get("x", 0))
        y += float(box.get("y", 0))
        parent = by_id[parent].get("parent")
    return x, y, float(geometry["width"]), float(geometry["height"])


class Canvas:
    def __init__(self, width: float, height: float) -> None:
        self.width, self.height = width, height
        self.parts: list[str] = []

    def rect(
        self,
        box,
        fill,
        stroke,
        stroke_width=1.0,
        radius=0.0,
        dashed=False,
        dash_pattern=None,
    ) -> None:
        x, y, w, h = box
        dash = f' stroke-dasharray="{dash_pattern or "6 4"}"' if dashed else ""
        self.parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{radius:.1f}"'
            f' fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{stroke_width}"{dash}/>'
        )

    def image(self, box, href: str, preserve: str = "xMidYMid meet") -> None:
        x, y, w, h = box
        self.parts.append(
            f'<image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"'
            f' preserveAspectRatio="{preserve}" xlink:href="{href}"/>'
        )

    def text(self, x, y, text, size, bold, color, anchor="start") -> None:
        weight = ' font-weight="bold"' if bold else ""
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size:g}"'
            f' fill="{color}" text-anchor="{anchor}"{weight}>{html.escape(text)}</text>'
        )

    def polyline(self, points, color, width, dashed) -> None:
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        self.parts.append(
            f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="{width}"{dash}/>'
        )
        self._arrow_head(points[-2], points[-1], color)

    def _arrow_head(self, previous, tip, color: str, size: float = 7.0) -> None:
        """Draw a triangle at the end of a line, pointing away from ``previous``."""
        run_x, run_y = tip[0] - previous[0], tip[1] - previous[1]
        length = max((run_x**2 + run_y**2) ** 0.5, 0.001)
        # Unit vector along the line, and the same vector turned 90 degrees.
        along_x, along_y = run_x / length * size, run_y / length * size
        across_x, across_y = -along_y * 0.45, along_x * 0.45
        base_x, base_y = tip[0] - along_x, tip[1] - along_y
        corners = [
            tip,
            (base_x + across_x, base_y + across_y),
            (base_x - across_x, base_y - across_y),
        ]
        points = " ".join(f"{x:.1f},{y:.1f}" for x, y in corners)
        self.parts.append(f'<polygon points="{points}" fill="{color}"/>')

    def render(self, content: str | None = None) -> str:
        # Draw.io stores the editable diagram in the SVG's content attribute; an
        # export written with it stays re-importable into Draw.io.
        embedded = f" content={quoteattr(content)}" if content else ""
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'
            f' width="{self.width:.0f}" height="{self.height:.0f}"'
            f' viewBox="0 0 {self.width:.0f} {self.height:.0f}"{embedded}>\n'
            f'<rect width="100%" height="100%" fill="#FFFFFF"/>\n'
            + "\n".join(self.parts)
            + "\n</svg>\n"
        )


def draw_label(canvas: Canvas, box, value: str, style: dict[str, str]) -> None:
    lines = label_lines(value, style)
    if not lines:
        return
    x, y, width, height = box
    line_heights = [text_layout.line_height(line.size) for line in lines]
    align = style.get("align", "center")

    if style.get("verticalAlign", "middle") == "top":
        cursor = y
    else:
        cursor = y + (height - sum(line_heights)) / 2

    for line, line_height in zip(lines, line_heights):
        baseline = cursor + line_height / 2 + line.size * 0.36
        if align == "left":
            canvas.text(x + 2, baseline, line.text, line.size, line.bold, line.color, "start")
        elif align == "right":
            canvas.text(x + width - 2, baseline, line.text, line.size, line.bold, line.color, "end")
        else:
            canvas.text(
                x + width / 2, baseline, line.text, line.size, line.bold, line.color, "middle"
            )
        cursor += line_height


def route(source, target, waypoints) -> list[tuple[float, float]]:
    """Approximate Draw.io's orthogonal routing, clipped to both rectangles."""
    sx, sy, sw, sh = source
    tx, ty, tw, th = target
    start, end = (sx + sw / 2, sy + sh / 2), (tx + tw / 2, ty + th / 2)
    if waypoints:
        points = [start, *waypoints, end]
    elif abs(end[0] - start[0]) >= abs(end[1] - start[1]):
        mid = (sx + sw + tx) / 2 if end[0] > start[0] else (tx + tw + sx) / 2
        points = [start, (mid, start[1]), (mid, end[1]), end]
    else:
        mid = (sy + sh + ty) / 2 if end[1] > start[1] else (ty + th + sy) / 2
        points = [start, (start[0], mid), (end[0], mid), end]

    squared: list[tuple[float, float]] = [points[0]]
    for point in points[1:]:
        last = squared[-1]
        if abs(point[0] - last[0]) > 0.5 and abs(point[1] - last[1]) > 0.5:
            squared.append((point[0], last[1]))
        squared.append(point)

    def inside(point, box) -> bool:
        x, y, w, h = box
        return x - 0.5 <= point[0] <= x + w + 0.5 and y - 0.5 <= point[1] <= y + h + 0.5

    while len(squared) > 2 and inside(squared[1], source):
        squared.pop(0)
    while len(squared) > 2 and inside(squared[-2], target):
        squared.pop()
    squared[0] = _on_border(squared[1], squared[0], source)
    squared[-1] = _on_border(squared[-2], squared[-1], target)
    return squared


def _on_border(outer, inner, box) -> tuple[float, float]:
    x, y, w, h = box
    if abs(outer[1] - inner[1]) < 0.5:
        return (x + w, inner[1]) if outer[0] > inner[0] else (x, inner[1])
    if abs(outer[0] - inner[0]) < 0.5:
        return (inner[0], y + h) if outer[1] > inner[1] else (inner[0], y)
    return inner


def _midpoint(points) -> tuple[float, float]:
    lengths = [abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(points, points[1:])]
    remaining = sum(lengths) / 2
    for index, length in enumerate(lengths):
        if remaining <= length:
            first, second = points[index], points[index + 1]
            ratio = remaining / length if length else 0
            return (first[0] + (second[0] - first[0]) * ratio, first[1] + (second[1] - first[1]) * ratio)
        remaining -= length
    return points[len(points) // 2]


def _stencil_data_uri(svg_text: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg_text.encode("utf-8")).decode("ascii")


def _missing_stencil(kind: str, key: str) -> ValueError:
    if key.startswith("mxgraph."):
        family_shape = key.removeprefix("mxgraph.").replace(".", "/", 1)
    elif key.startswith("img/lib/"):
        # maintenance/render_stencils.py accepts an Azure library path relative
        # to img/lib, such as azure2/containers/Container_Registries.svg.
        family_shape = key.removeprefix("img/lib/")
    else:
        family_shape = key
    return ValueError(
        f"no pre-rendered SVG for {kind} {key!r}. Run "
        f"'sh <skill-dir>/scripts/run_python.sh <skill-dir>/maintenance/render_stencils.py {family_shape}' once "
        "(network required) and re-export; the .drawio itself is already complete"
    )


def build_svg(
    drawio: Path,
    tokens: dict[str, Any],
    stencil_svgs: dict[str, str] | None = None,
    strict: bool = False,
    content: str | None = None,
) -> str:
    """Draw the diagram as SVG.

    Without ``stencil_svgs`` this is a layout proof: app-only stencils appear as
    placeholders. With ``stencil_svgs`` (from ``assets/icon-styles.json``) every
    icon renders for real; ``strict`` turns any icon that still cannot be drawn
    into an error so an export never silently degrades.
    """
    stencil_svgs = stencil_svgs or {}
    model = read_graph_model(read_mxfile(drawio))
    cells = graph_inventory(model)["cells"]
    by_id = {cell["id"]: cell for cell in cells if cell.get("id")}
    canvas = Canvas(
        float(model.attrib.get("pageWidth", 1600)), float(model.attrib.get("pageHeight", 1000))
    )

    for cell in cells:
        box = absolute(cell, by_id) if cell.get("vertex") else None
        if box is None:
            continue
        style = parse_style(cell.get("style", "") or "")
        shape = style.get("shape", "")
        if shape == "image" and "image" in style:
            href = cell["style"].split("image=", 1)[1].split(";", 1)[0]
            if href.startswith("data:image/svg+xml,"):
                # Draw.io writes the base64 payload straight after the comma. Other
                # renderers only decode it when the ";base64" marker is present.
                href = href.replace("data:image/svg+xml,", "data:image/svg+xml;base64,", 1)
            elif not href.startswith("data:"):
                # Bundled app images (Azure): substitute the pre-rendered copy.
                if href in stencil_svgs:
                    href = _stencil_data_uri(stencil_svgs[href])
                elif strict:
                    raise _missing_stencil("image", href)
                else:
                    canvas.rect(box, "#E8F0FE", "#4284F3", 1, 3)
                    continue
            canvas.image(box, href)
            continue
        if shape.startswith("mxgraph.") and cell.get("data_kind") != "container":
            if shape in stencil_svgs:
                # aspect=fixed in the icon styles, so scale preserving aspect.
                canvas.image(box, _stencil_data_uri(stencil_svgs[shape]))
            elif strict:
                raise _missing_stencil("stencil", shape)
            else:
                # A Draw.io stencil only exists inside the app; show where it will sit.
                canvas.rect(box, "#E8F0FE", "#4284F3", 1, 3)
            continue
        if shape == "line":
            x, y, w, h = box
            canvas.polyline(
                [(x, y + h / 2), (x + w, y + h / 2)],
                style.get("strokeColor", "#000000"),
                float(style.get("strokeWidth", 1)),
                style.get("dashed") == "1",
            )
            continue
        if "text" not in style:
            radius = 2.0 if style.get("absoluteArcSize") == "1" else 0.0
            stroke = style.get("strokeColor", "#000000")
            if style.get("grStroke") == "0":
                # AWS Groupsのサブネット表現。枠線は描かず塗りだけで領域を示す。
                stroke = "none"
            canvas.rect(
                box,
                style.get("fillColor", "none"),
                stroke,
                float(style.get("strokeWidth", 1) or 1),
                radius,
                style.get("dashed") == "1",
                style.get("dashPattern"),
            )
            if style.get("grIcon"):
                # AWS Groupsの角アイコン。25px四方、グループの線色で塗られる。
                icon_key = style["grIcon"]
                if icon_key in stencil_svgs:
                    recolored = re.sub(
                        r'fill="#[0-9A-Fa-f]+"',
                        f'fill="{style.get("strokeColor", "#232F3E")}"',
                        stencil_svgs[icon_key],
                    )
                    canvas.image((box[0], box[1], 25, 25), _stencil_data_uri(recolored))
                elif strict:
                    raise _missing_stencil("group icon", icon_key)
                else:
                    canvas.rect(
                        (box[0], box[1], 25, 25), style.get("strokeColor", "#000000"), "none", 0
                    )
        draw_label(canvas, box, cell.get("value", "") or "", style)

    for cell in cells:
        if not cell.get("edge"):
            continue
        source, target = by_id.get(cell.get("source") or ""), by_id.get(cell.get("target") or "")
        if not source or not target:
            continue
        source_box, target_box = absolute(source, by_id), absolute(target, by_id)
        if source_box is None or target_box is None:
            continue
        style = parse_style(cell.get("style", "") or "")
        token = tokens["edges"].get(cell.get("edge_kind") or "dependency", tokens["edges"]["dependency"])
        points = route(
            source_box,
            target_box,
            [(float(point["x"]), float(point["y"])) for point in cell.get("waypoints", [])],
        )
        canvas.polyline(
            points,
            style.get("strokeColor", token["stroke"]),
            float(style.get("strokeWidth", token["width"]) or token["width"]),
            style.get("dashed") == "1",
        )
        text = html.unescape(TAG_RE.sub("", cell.get("value") or ""))
        if text:
            x, y = _midpoint(points)
            # Match Draw.io's opaque label background so collisions show up here.
            width = text_layout.measure(text, 11) + 10
            canvas.rect((x - width / 2, y - 9, width, 18), "#FFFFFF", "none", 0)
            canvas.text(x, y + 4, text, 11, False, "#202124", "middle")

    return canvas.render(content)


def rasterize(svg: Path, png: Path, width: int) -> str:
    """Turn the preview SVG into a PNG with whichever local rasteriser exists."""
    if shutil.which("rsvg-convert"):
        subprocess.run(
            ["rsvg-convert", "--width", str(width), "--keep-aspect-ratio",
             "--background-color", "white", "--output", str(png), str(svg)],
            check=True,
        )
        return "rsvg-convert"
    if shutil.which("qlmanage"):
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run(
                ["qlmanage", "-t", "-s", str(width), "-o", temp, str(svg)],
                check=False, capture_output=True,
            )
            produced = next(Path(temp).glob("*.png"), None)
            if produced:
                png.write_bytes(produced.read_bytes())
                return "qlmanage"
    raise ValueError(
        "no SVG rasteriser found. Install librsvg (rsvg-convert), or open the preview SVG "
        "in a browser or the VS Code Draw.io extension and look at it there."
    )


def write_preview(drawio: Path, png: Path, tokens: dict[str, Any], width: int = 1800) -> str:
    # Best-effort icon substitution: stencils with a pre-rendered copy show for
    # real, the rest stay placeholders. The preview never fails over icons.
    try:
        catalog = json.loads((SKILL_DIR / "assets" / "icon-styles.json").read_text(encoding="utf-8"))
        stencil_svgs = catalog.get("stencil_svgs", {})
    except (OSError, json.JSONDecodeError):
        stencil_svgs = {}
    svg = png.with_suffix(".svg")
    svg.parent.mkdir(parents=True, exist_ok=True)
    svg.write_text(build_svg(drawio, tokens, stencil_svgs=stencil_svgs), encoding="utf-8")
    renderer = rasterize(svg, png, width)
    return f"{png} via {renderer} (SVG at {svg})"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a layout preview from a .drawio file")
    parser.add_argument("drawio", type=Path)
    parser.add_argument("--png", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1800)
    parser.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS)
    args = parser.parse_args()
    try:
        tokens = json.loads(args.tokens.read_text(encoding="utf-8"))
        print(f"wrote {write_preview(args.drawio, args.png, tokens, args.width)}")
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
