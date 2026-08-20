#!/usr/bin/env python3

"""Export architecture.svg from architecture.drawio without the Draw.io app.

The Draw.io CLI is not available in this environment and the VS Code extension
has no headless export, so this renders the SVG directly: the same renderer the
preview uses, plus two things a preview does not need — every icon drawn for
real (app-only stencils come from the pre-rendered copies in
``assets/icon-styles.json``) and the editable diagram XML embedded in the SVG's
``content`` attribute, so Draw.io can re-import the file.

An icon without a pre-rendered copy fails the export with instructions to run
``maintenance/render_stencils.py``; a silently degraded artifact is worse than
none. The ``.drawio`` remains the canonical artifact either way, and a manual
File > Export from the VS Code extension is always a valid substitute.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import preview

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TOKENS = SKILL_DIR / "assets" / "style-tokens.json"
DEFAULT_ICONS = SKILL_DIR / "assets" / "icon-styles.json"


def export(drawio: Path, output: Path, tokens_path: Path, icons_path: Path) -> None:
    tokens = json.loads(tokens_path.read_text(encoding="utf-8"))
    stencil_svgs = json.loads(icons_path.read_text(encoding="utf-8")).get("stencil_svgs", {})
    svg = preview.build_svg(
        drawio,
        tokens,
        stencil_svgs=stencil_svgs,
        strict=True,
        content=drawio.read_text(encoding="utf-8"),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export an SVG from a .drawio, no Draw.io app needed")
    parser.add_argument("drawio", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS)
    parser.add_argument("--icons", type=Path, default=DEFAULT_ICONS)
    args = parser.parse_args()
    try:
        export(args.drawio, args.output, args.tokens, args.icons)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {args.output} (editable copy embedded in the content attribute)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
