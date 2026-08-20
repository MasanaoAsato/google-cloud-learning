#!/usr/bin/env python3

"""Draw.ioサイドバーの埋め込み画像アイコンをカタログへ機械的に取り込む。

Draw.io本体は、ステンシル化されていない新しめのサービス（Artifact Registry、
Eventarc、Secret Managerなど）を、サイドバーJSの中に`image=data:image/svg+xml,...`
形式で直接埋め込んでいる。このスクリプトはそのサイドバーJSを取得・パースし、
指定した名前のアイコンを`assets/icon-styles.json`の`sidebar_images`へ書き込む。
手作業のharvestと違い、供給源がjgraph/drawioリポジトリに一本化され、再実行で
上流へ追従できる。

    sh scripts/run_python.sh maintenance/sync_sidebar_icons.py                    # 既存sidebar_imagesを上流で更新
    sh scripts/run_python.sh maintenance/sync_sidebar_icons.py gcp/"Eventarc"     # 名前を指定して追加

名前はサイドバーのタイトルと大文字小文字・空白を無視して照合する。取り込み後は
`scripts/self_test.py`を実行すること。
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

SKILL_DIR = Path(__file__).resolve().parents[1]
CATALOG = SKILL_DIR / "assets" / "icon-styles.json"
UPSTREAM = "https://raw.githubusercontent.com/jgraph/drawio/dev/src/main/webapp/js/diagramly/sidebar"

# プロバイダごとの取得元サイドバー。画像埋め込みエントリを持つものだけを挙げる。
SIDEBAR_SOURCES: dict[str, list[str]] = {
    "gcp": ["Sidebar-GCP2.js", "Sidebar-GCPIcons.js"],
    "aws": ["Sidebar-AWS4.js", "Sidebar-AWS4b.js"],
    "azure": ["Sidebar-Azure2.js"],
}

IMAGE_MARKER = "image=data:image/svg+xml,"
# 生成する style は既存カタログと同じ「カード内アイコン用」の接頭辞に統一する。
STYLE_PREFIX = "editableCssRules=.*;html=1;shape=image;aspect=fixed;imageAspect=0;"

sys.path.insert(0, str(SKILL_DIR / "maintenance"))
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from sync_upstream import call_arguments, eval_string_expr, fetch, unquote  # noqa: E402
from icon_catalog import canonical  # noqa: E402

VAR_RE = re.compile(r"var\s+([A-Za-z_$][\w$]*)\s*=\s*('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")\s*;")


def palette_blocks(source: str) -> list[str]:
    """Sidebar.prototype.addXxxPalette = function ... のブロックへ分割する。"""
    starts = [match.start() for match in re.finditer(r"Sidebar\.prototype\.\w+ = function", source)]
    starts.append(len(source))
    return [source[starts[i] : starts[i + 1]] for i in range(len(starts) - 1)]


def string_literal(arg: str) -> str | None:
    """引用符付きリテラルなら中身を返す。識別子やnullはNone。`\\n`は空白へ畳む。"""
    arg = arg.strip()
    if len(arg) >= 2 and arg[0] in "'\"" and arg[-1] == arg[0]:
        return arg[1:-1].replace("\\n", " ")
    return None


def image_entries(source: str) -> dict[str, str]:
    """タイトル(canonical) → base64 SVG。画像埋め込みのvertexエントリだけを拾う。"""
    entries: dict[str, str] = {}
    for block in palette_blocks(source):
        substitutions = {name: unquote(value) for name, value in VAR_RE.findall(block)}
        for args in call_arguments(block, "this.createVertexTemplateEntry"):
            if len(args) < 5:
                continue
            try:
                style = eval_string_expr(args[0], substitutions)
            except ValueError:
                continue
            if IMAGE_MARKER not in style:
                continue
            title = string_literal(args[4]) or string_literal(args[3]) or ""
            name = canonical(title)
            if not name or name in entries:
                continue
            encoded = style.split(IMAGE_MARKER, 1)[1].split(";", 1)[0]
            try:
                ET.fromstring(base64.b64decode(encoded, validate=True))
            except (ValueError, ET.ParseError):
                continue
            entries[name] = encoded
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "names", nargs="*", metavar="PROVIDER/NAME",
        help="取り込む名前（例: gcp/Eventarc）。省略時は既存sidebar_imagesを更新",
    )
    args = parser.parse_args()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    images: dict[str, dict[str, str]] = catalog.setdefault("sidebar_images", {})

    wanted: dict[str, set[str]] = {provider: set() for provider in SIDEBAR_SOURCES}
    if args.names:
        for entry in args.names:
            provider, _, name = entry.partition("/")
            if provider not in SIDEBAR_SOURCES or not name:
                print(f"ERROR: unknown target {entry!r}; use provider/name", file=sys.stderr)
                return 2
            wanted[provider].add(canonical(name))
    else:
        for name, icon in images.items():
            provider = icon.get("provider")
            if provider in wanted:
                wanted[provider].add(name)
        if not any(wanted.values()):
            print("nothing to sync: sidebar_images is empty and no names were given")
            return 0

    written = 0
    for provider, names in wanted.items():
        if not names:
            continue
        remaining = set(names)
        for filename in SIDEBAR_SOURCES[provider]:
            if not remaining:
                break
            entries = image_entries(fetch(f"{UPSTREAM}/{filename}"))
            for name in sorted(remaining & set(entries)):
                images[name] = {
                    "provider": provider,
                    "style": f"{STYLE_PREFIX}{IMAGE_MARKER}{entries[name]};",
                    "source_label": f"Draw.io sidebar image ({filename})",
                }
                remaining.discard(name)
                written += 1
                print(f"+ {provider}/{name} <- {filename}")
        for missing in sorted(remaining):
            print(f"ERROR: {provider} sidebar image {missing!r} not found upstream", file=sys.stderr)

    catalog["sidebar_images"] = dict(sorted(images.items()))
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {CATALOG}: {len(images)} sidebar image(s), {written} updated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
