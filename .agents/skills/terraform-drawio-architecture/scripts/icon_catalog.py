#!/usr/bin/env python3

"""Resolve a service or subject name to a real Draw.io icon style.

Two rules shape this module. First, a diagram reads fastest when its shapes are
the ones Draw.io itself offers, so resolution prefers the standard libraries.
Second, a made-up style string produces a blank shape in Draw.io, which is worse
than no icon at all — so every style here comes from a verified source, in this
order (the same policy for AWS, Azure, and GCP):

1. ``stencils``: shapes checked against Draw.io's own shape libraries, including
   the generic subjects (users, laptop, internet, external data centre) that let
   people and networks be drawn with the same icon family as services.
2. ``sidebar_images``: SVG icons that Draw.io embeds directly in its sidebar for
   services that have no stencil yet (kept in sync mechanically by
   ``maintenance/sync_sidebar_icons.py``; ``--harvest`` below adds icons from
   human-drawn files as a manual fallback).
3. Nothing matches: ``resolve`` raises ``KeyError`` with the closest catalog
   names; the builder then draws a plain box with the service name instead of
   inventing a style.
"""

from __future__ import annotations

import base64
import difflib
import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = SKILL_DIR / "assets" / "icon-styles.json"
IMAGE_MARKER = "image=data:image/svg+xml,"
TAG_RE = re.compile(r"<[^>]+>")


def canonical(name: str) -> str:
    text = TAG_RE.sub(" ", name)
    text = text.replace("　", " ").replace("\n", " ")
    text = re.sub(r"[（）()]", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def stencil_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", canonical(name)).strip("_")


class IconCatalog:
    def __init__(self, data: dict[str, Any]) -> None:
        self.sidebar_images: dict[str, dict[str, str]] = data.get("sidebar_images", {})
        self.stencils: dict[str, dict[str, Any]] = data.get("stencils", {})
        self.aliases: dict[str, str] = {
            canonical(key): value for key, value in data.get("aliases", {}).items()
        }
        for name, icon in self.sidebar_images.items():
            style = icon.get("style", "")
            if IMAGE_MARKER not in style:
                raise ValueError(f"sidebar image {name!r} is not a Draw.io image style")
            encoded = style.split(IMAGE_MARKER, 1)[1].rstrip(";")
            try:
                ET.fromstring(base64.b64decode(encoded, validate=True))
            except (ValueError, ET.ParseError) as exc:
                raise ValueError(f"sidebar image {name!r} has invalid SVG data: {exc}") from exc

    @classmethod
    def load(cls, path: Path = DEFAULT_CATALOG) -> "IconCatalog":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read icon catalog: {exc}") from exc
        return cls(data)

    def names(self) -> list[str]:
        names = list(self.sidebar_images) + list(self.aliases)
        for stencil in self.stencils.values():
            names.extend(shape.replace("_", " ") for shape in stencil.get("shapes", []))
        return sorted(set(names))

    def suggest(self, name: str, limit: int = 6) -> list[str]:
        return difflib.get_close_matches(canonical(name), self.names(), n=limit, cutoff=0.5)

    def _candidates(self, name: str) -> list[str]:
        key = canonical(name)
        alias = self.aliases.get(key)
        if alias is None:
            return [key]
        return [alias] if isinstance(alias, str) else list(alias)

    def _library_order(self, provider: str | None) -> list[str]:
        """Prefer the diagram's own cloud so a GCP figure never borrows an AWS icon."""
        preferred = [
            name
            for name, stencil in self.stencils.items()
            if provider and stencil.get("provider") == provider
        ]
        return preferred + [name for name in self.stencils if name not in preferred]

    def resolve(self, name: str, provider: str | None = None) -> tuple[str, str]:
        """Return (style, source label) for a service or subject name.

        Standard shape libraries come first so diagrams use the same cards and
        stencils the Draw.io sidebar offers; sidebar images fill the gaps for
        services that have no stencil yet.
        """
        candidates = self._candidates(name)

        for library in self._library_order(provider):
            stencil = self.stencils[library]
            shapes = stencil.get("shapes", {})
            for key in candidates:
                shape = stencil_key(key)
                if shape in shapes:
                    style = stencil["style_template"].format(shape=shapes[shape])
                    return style.rstrip(";") + ";", f"Draw.io {library} shape {shape}"

        for key in candidates:
            icon = self.sidebar_images.get(key)
            if icon is None:
                continue
            # Respect the diagram's cloud: a GCP figure must not borrow an AWS icon.
            if provider and icon.get("provider") and icon["provider"] != provider:
                continue
            return icon["style"].rstrip(";") + ";", icon.get("source_label", key)

        raise KeyError(name)


def resolve_or_raise(
    catalog: IconCatalog, name: str, context: str, provider: str | None = None
) -> tuple[str, str]:
    try:
        return catalog.resolve(name, provider)
    except KeyError:
        suggestions = catalog.suggest(name)
        hint = f" Closest catalog names: {', '.join(suggestions)}." if suggestions else ""
        raise ValueError(
            f"{context}: no Draw.io icon in the catalog for {name!r}.{hint} "
            "Either use one of those names, fetch the icon with "
            "maintenance/sync_sidebar_icons.py, harvest it from a Draw.io file with "
            "icon_catalog.py --harvest, or let the builder draw a plain box and "
            "record the reason in architecture-notes.md."
        ) from None


def harvest(paths: list[Path], catalog_path: Path = DEFAULT_CATALOG) -> int:
    """Add icons from diagrams a human drew in Draw.io to the catalog.

    The mechanical route is ``maintenance/sync_sidebar_icons.py``, which pulls the
    same artwork straight from the Draw.io sidebar sources. Harvesting stays as the
    manual fallback for icons that never appear there: any diagram already using an
    icon carries an exact copy of it in its ``image=data:image/svg+xml,...`` style,
    and the label the human typed becomes the lookup name.
    """
    from inspect_drawio import graph_inventory, read_graph_model, read_mxfile

    files: list[Path] = []
    for item in paths:
        if item.is_dir():
            files.extend(sorted(item.rglob("*.drawio")))
            files.extend(sorted(item.rglob("*.svg")))
        else:
            files.append(item)

    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    added = 0
    for path in files:
        try:
            cells = graph_inventory(read_graph_model(read_mxfile(path)))["cells"]
        except ValueError:
            continue
        for cell in cells:
            style = cell.get("style", "") or ""
            if IMAGE_MARKER not in style:
                continue
            encoded = style.split(IMAGE_MARKER, 1)[1].split(";", 1)[0]
            try:
                ET.fromstring(base64.b64decode(encoded, validate=True))
            except (ValueError, ET.ParseError):
                continue
            name = canonical(cell.get("value", "") or "")
            if not name:
                print(f"? unlabelled icon skipped: {path}#{cell.get('id')}")
                continue
            if name in data["sidebar_images"]:
                continue
            data["sidebar_images"][name] = {
                "style": "editableCssRules=.*;html=1;shape=image;aspect=fixed;imageAspect=0;"
                f"{IMAGE_MARKER}{encoded};",
                "source_label": f"Draw.io icon harvested from {path.name}",
            }
            added += 1
            print(f"+ {name}")
    data["sidebar_images"] = dict(sorted(data["sidebar_images"].items()))
    catalog_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {catalog_path}: {len(data['sidebar_images'])} sidebar image(s), {added} new")
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Inspect or extend the Draw.io icon catalog")
    parser.add_argument("names", nargs="*", help="service or subject names to resolve")
    parser.add_argument("--provider", choices=["aws", "azure", "gcp"])
    parser.add_argument(
        "--harvest", type=Path, nargs="+", metavar="PATH",
        help=".drawio/.svg files or directories to harvest icon styles from",
    )
    args = parser.parse_args()

    if args.harvest:
        return harvest(args.harvest)

    catalog = IconCatalog.load()
    if not args.names:
        print(f"sidebar images: {len(catalog.sidebar_images)}")
        for library, stencil in catalog.stencils.items():
            print(f"{library} ({stencil.get('provider')}): {len(stencil.get('shapes', {}))} shapes")
        print(f"aliases: {len(catalog.aliases)}")
        return 0
    for name in args.names:
        try:
            style, source = catalog.resolve(name, args.provider)
            print(f"{name!r} -> {source}\n  {style[:96]}...")
        except KeyError:
            print(f"{name!r} -> not found; closest: {catalog.suggest(name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
