#!/usr/bin/env python3

"""Pre-render Draw.io stencil shapes to standalone SVG for the skill's exporter.

Draw.io built-in stencils (``shape=mxgraph.gcp2.users`` and friends) only render
inside the Draw.io app, which is why the skill could not export an SVG without
the Draw.io CLI. Their definitions, however, are plain path data in the
jgraph/drawio repository (Apache-2.0). This script fetches those definitions,
converts each needed shape into a small self-contained SVG, and stores it in
``assets/icon-styles.json`` under ``stencil_svgs``. ``scripts/export_svg.py``
then substitutes these renderings for the app-only stencils, so SVG export works
offline with no CLI.

Run it when the exporter reports a missing stencil rendering:

    sh scripts/run_python.sh maintenance/render_stencils.py            # all alias-reachable shapes
    sh scripts/run_python.sh maintenance/render_stencils.py gcp2/users # specific shapes

Azure icons are bundled SVG files in the same repository, so they are fetched
verbatim instead of converted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

SKILL_DIR = Path(__file__).resolve().parents[1]
CATALOG = SKILL_DIR / "assets" / "icon-styles.json"
TOKENS = SKILL_DIR / "assets" / "style-tokens.json"
UPSTREAM = "https://raw.githubusercontent.com/jgraph/drawio/dev/src/main/webapp"
STENCIL_FILES = {"gcp2": "stencils/gcp2.xml", "aws4": "stencils/aws4.xml"}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": "terraform-drawio-architecture-render-stencils"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def normalized(name: str) -> str:
    """Draw.io registers a stencil as lowercase with spaces as underscores."""
    return name.lower().replace(" ", "_")


def path_data(element: ET.Element) -> str:
    parts: list[str] = []
    for op in element:
        tag = op.tag
        get = op.get
        if tag == "move":
            parts.append(f"M {get('x')} {get('y')}")
        elif tag == "line":
            parts.append(f"L {get('x')} {get('y')}")
        elif tag == "curve":
            parts.append(
                f"C {get('x1')} {get('y1')} {get('x2')} {get('y2')} {get('x3')} {get('y3')}"
            )
        elif tag == "quad":
            parts.append(f"Q {get('x1')} {get('y1')} {get('x2')} {get('y2')}")
        elif tag == "arc":
            parts.append(
                f"A {get('rx')} {get('ry')} {get('x-axis-rotation', '0')} "
                f"{get('large-arc-flag', '0')} {get('sweep-flag', '0')} {get('x')} {get('y')}"
            )
        elif tag == "close":
            parts.append("Z")
    return " ".join(parts)


def shape_to_svg(shape: ET.Element, default_fill: str) -> str:
    """Interpret the stencil drawing ops that Draw.io's own renderer supports.

    Fills follow the style's fillColor unless the stencil overrides them; stroke
    ops are honoured only when the stencil sets a stroke colour, because the
    skill's icon styles use ``strokeColor=none``.
    """
    width = float(shape.get("w", "100"))
    height = float(shape.get("h", "100"))
    state = {"fill": default_fill, "stroke": None, "fill_alpha": 1.0, "stroke_width": 1.0}
    stack: list[dict] = []
    current = ""
    emitted: list[str] = []

    def paint(fill: bool, stroke: bool) -> None:
        if not current:
            return
        attrs = [f'd="{current}"']
        attrs.append(f'fill="{state["fill"]}"' if fill else 'fill="none"')
        if fill and state["fill_alpha"] < 1.0:
            attrs.append(f'fill-opacity="{state["fill_alpha"]:g}"')
        if stroke and state["stroke"]:
            attrs.append(f'stroke="{state["stroke"]}" stroke-width="{state["stroke_width"]:g}"')
        if fill or (stroke and state["stroke"]):
            emitted.append(f"<path {' '.join(attrs)}/>")

    for section_name in ("background", "foreground"):
        section = shape.find(section_name)
        if section is None:
            continue
        for op in section:
            tag = op.tag
            if tag == "save":
                stack.append(dict(state))
            elif tag == "restore":
                if stack:
                    state.clear()
                    state.update(stack.pop())
            elif tag == "path":
                current = path_data(op)
            elif tag == "rect":
                x = float(op.get("x", 0)); y = float(op.get("y", 0))
                w = float(op.get("w", width)); h = float(op.get("h", height))
                current = f"M {x} {y} L {x + w} {y} L {x + w} {y + h} L {x} {y + h} Z"
            elif tag == "ellipse":
                x = float(op.get("x", 0)); y = float(op.get("y", 0))
                w = float(op.get("w", width)); h = float(op.get("h", height))
                rx, ry, cy = w / 2, h / 2, y + h / 2
                current = (
                    f"M {x} {cy} A {rx} {ry} 0 1 0 {x + w} {cy} A {rx} {ry} 0 1 0 {x} {cy} Z"
                )
            elif tag == "fillcolor":
                state["fill"] = op.get("color", default_fill)
            elif tag == "strokecolor":
                state["stroke"] = op.get("color")
            elif tag == "fillalpha":
                state["fill_alpha"] = float(op.get("alpha", "1"))
            elif tag == "strokewidth":
                state["stroke_width"] = float(op.get("width", "1"))
            elif tag == "fill":
                paint(fill=True, stroke=False)
            elif tag == "stroke":
                paint(fill=False, stroke=True)
            elif tag == "fillstroke":
                paint(fill=True, stroke=True)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}">'
        + "".join(emitted)
        + "</svg>"
    )


def alias_reachable_shapes(catalog: dict) -> dict[str, set[str]]:
    """Shape names each family can serve through the catalog's alias table."""
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    from icon_catalog import canonical, stencil_key

    candidates: set[str] = set()
    for value in catalog.get("aliases", {}).values():
        values = [value] if isinstance(value, str) else value
        candidates.update(canonical(item) for item in values)
    reachable: dict[str, set[str]] = {}
    for family, stencil in catalog.get("stencils", {}).items():
        shapes = stencil.get("shapes", {})
        reachable[family] = {
            shapes[stencil_key(item)] for item in candidates if stencil_key(item) in shapes
        }
    return reachable


def aws_group_icons() -> set[str]:
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    groups = tokens.get("providers", {}).get("aws", {}).get("groups", {})
    return {value["icon"] for value in groups.values() if isinstance(value, dict) and value.get("icon")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "shapes", nargs="*",
        help="family/shape entries such as gcp2/users; default is every alias-reachable shape",
    )
    args = parser.parse_args()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    targets: dict[str, set[str]] = {family: set() for family in catalog.get("stencils", {})}
    if args.shapes:
        for entry in args.shapes:
            family, _, shape = entry.partition("/")
            if family not in targets or not shape:
                print(f"ERROR: unknown target {entry!r}; use family/shape", file=sys.stderr)
                return 2
            targets[family].add(shape)
    else:
        for family, shapes in alias_reachable_shapes(catalog).items():
            targets[family] |= shapes
        targets.setdefault("aws4", set())
        targets["aws4"] |= aws_group_icons()

    renderings = catalog.setdefault("stencil_svgs", {})
    written = 0

    for family, filename in STENCIL_FILES.items():
        wanted = {normalized(shape) for shape in targets.get(family, set())}
        if not wanted:
            continue
        default_fill = re.search(
            r"fillColor=(#[0-9A-Fa-f]+)", catalog["stencils"][family]["style_template"]
        ).group(1)
        root = ET.fromstring(fetch(f"{UPSTREAM}/{filename}"))
        found: set[str] = set()
        for shape in root.iter("shape"):
            name = normalized(shape.get("name", ""))
            if name not in wanted:
                continue
            key = f"mxgraph.{family}.{name}"
            renderings[key] = shape_to_svg(shape, default_fill)
            found.add(name)
            written += 1
            print(f"+ {key}")
        for missing in sorted(wanted - found):
            print(f"ERROR: {family} stencil {missing!r} not found upstream", file=sys.stderr)

    azure_targets = targets.get("azure2", set())
    for shape_path in sorted(azure_targets):
        # ``shape_path`` is relative to the Azure library family, for example
        # ``containers/Container_Registries.svg``.  Keep that family in both
        # the catalog key and the upstream URL; omitting it causes a 404.
        key = f"img/lib/azure2/{shape_path}"
        svg = fetch(f"{UPSTREAM}/{key}").decode("utf-8")
        renderings[key] = svg
        written += 1
        print(f"+ {key}")

    catalog["stencil_svgs"] = dict(sorted(renderings.items()))
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {CATALOG}: {len(catalog['stencil_svgs'])} stencil rendering(s), {written} updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
