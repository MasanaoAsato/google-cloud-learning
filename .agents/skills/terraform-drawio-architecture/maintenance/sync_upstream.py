#!/usr/bin/env python3

"""Draw.io上流とstyle-tokens.jsonの同期。

このスキルはAWSの境界を公式「AWS / Groups」、GCPの線を公式「GCP / Paths」で
描く。その色・grIcon・破線はjgraph/drawioのサイドバー定義が上流であり、値が
世代交代することがある（例: VPCは2019年の緑から現在の紫へ変わった）。

このスクリプトは上流のサイドバーJSを取得してパースし、`style-tokens.json`の
上流由来セクション（`providers.aws.groups`、`edges_gcp`）と突き合わせる。

    sh scripts/run_python.sh maintenance/sync_upstream.py --check  # 乖離を表示。乖離があれば終了コード2
    sh scripts/run_python.sh maintenance/sync_upstream.py --write  # style-tokens.jsonを上流へ追従させる

`providers.gcp`の塗りは「公式Zoneパレットから当スキルが選んだ割り当て」なので
書き換えず、選んだ色が上流パレットから消えていないかだけ検査する。可読性の
ための意図的な逸脱は`providers.aws.group_overrides`に置き、ここでは触らない。

--writeの後は必ず`self_test.py`を実行し、プレビュー画像で見た目を確認すること。
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TOKENS = SKILL_DIR / "assets" / "style-tokens.json"

# 上流のタイトル → providers.aws.groups のキー。
AWS_TITLE_TO_KIND = {
    "AWS Cloud": "cloud",
    "AWS Account": "account",
    "Region": "region",
    "Availability Zone": "zone",
    "VPC": "network",
    "Public subnet": "public_subnet",
    "Private subnet": "private_subnet",
    "Corporate data center": "external",
}

# 上流のタイトル → edges_gcp の構築で参照するキー。
GCP_PATH_TITLES = ("Primary Path", "Optional Primary Path", "Optional Secondary Path")


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "terraform-drawio-architecture-sync"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def function_block(source: str, name: str) -> str:
    start = source.index(f"Sidebar.prototype.{name} = function")
    end = source.find("Sidebar.prototype.", start + 1)
    return source[start : end if end > 0 else len(source)]


def split_top_level_args(text: str) -> list[str]:
    """関数呼び出しの引数リストを、引用符と括弧の深さを見てトップレベルで分割する。"""
    args: list[str] = []
    depth = 0
    quote: str | None = None
    current: list[str] = []
    for char in text:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in "'\"":
            quote = char
            current.append(char)
        elif char in "([{":
            depth += 1
            current.append(char)
        elif char in ")]}":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        args.append("".join(current).strip())
    return args


def call_arguments(block: str, marker: str) -> list[list[str]]:
    """`marker(` で始まる各呼び出しの引数を返す。"""
    calls: list[list[str]] = []
    index = 0
    while True:
        index = block.find(marker + "(", index)
        if index < 0:
            return calls
        cursor = index + len(marker) + 1
        depth = 1
        quote: str | None = None
        start = cursor
        while depth > 0:
            char = block[cursor]
            if quote:
                if char == quote:
                    quote = None
            elif char in "'\"":
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            cursor += 1
        calls.append(split_top_level_args(block[start : cursor - 1]))
        index = cursor


def eval_string_expr(expr: str, substitutions: dict[str, str]) -> str:
    """`n4 + 'a;' + gn + '.b;'` のような連結式を、識別子を置換しつつ文字列へ畳む。"""
    parts = split_plus(expr)
    resolved: list[str] = []
    for part in parts:
        part = part.strip()
        if len(part) >= 2 and part[0] in "'\"" and part[-1] == part[0]:
            resolved.append(part[1:-1])
        elif part in substitutions:
            resolved.append(substitutions[part])
        else:
            raise ValueError(f"cannot resolve identifier {part!r} in style expression: {expr!r}")
    return "".join(resolved)


def split_plus(expr: str) -> list[str]:
    parts: list[str] = []
    quote: str | None = None
    current: list[str] = []
    for char in expr:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
            current.append(char)
        elif char == "+":
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def style_fields(style: str) -> dict[str, str]:
    return {
        key: value
        for chunk in style.split(";")
        if "=" in chunk
        for key, value in [chunk.split("=", 1)]
    }


def unquote(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] in "'\"" and text[-1] == text[0]:
        return text[1:-1]
    return text


def parse_aws_groups(source: str) -> dict[str, dict[str, Any]]:
    block = function_block(source, "addAWS4GroupsPalette")
    substitutions = {"n4": "", "gn": "mxgraph.aws4", "pts": ""}
    groups: dict[str, dict[str, Any]] = {}
    for args in call_arguments(block, "this.createVertexTemplateEntry"):
        title = unquote(args[4])
        kind = AWS_TITLE_TO_KIND.get(title)
        if kind is None or kind in groups:  # 同名エントリ（AWS Cloudの別亜種）は先勝ち
            continue
        fields = style_fields(eval_string_expr(args[0], substitutions))
        icon = fields.get("grIcon")
        if icon and icon.startswith("mxgraph.aws4."):
            icon = icon[len("mxgraph.aws4.") :]
        group: dict[str, Any] = {
            "icon": icon,
            "stroke": fields.get("strokeColor"),
            "font": fields.get("fontColor"),
        }
        if fields.get("grStroke") == "0":
            group["fill"] = fields.get("fillColor")
            group["borderless"] = True
        else:
            group["dashed"] = fields.get("dashed") == "1"
        groups[kind] = group
    missing = sorted(set(AWS_TITLE_TO_KIND.values()) - set(groups))
    if missing:
        raise ValueError(f"AWS groups palette is missing expected entries: {missing}")
    return groups


def parse_gcp(source: str) -> tuple[dict[str, dict[str, Any]], set[str]]:
    block = function_block(source, "addGCP2PathsPalette")
    prefix_expr = block.split("var s = ", 1)[1].split(";\n", 1)[0]
    prefix = style_fields(unquote(prefix_expr.rstrip(";")))
    substitutions = {"s": ""}
    paths: dict[str, dict[str, str]] = {}
    for args in call_arguments(block, "this.createEdgeTemplateEntry"):
        title = unquote(args[4])
        if title in GCP_PATH_TITLES:
            paths[title] = style_fields(eval_string_expr(args[0], substitutions))
    missing = sorted(set(GCP_PATH_TITLES) - set(paths))
    if missing:
        raise ValueError(f"GCP paths palette is missing expected entries: {missing}")

    base = {
        "width": int(prefix["strokeWidth"]),
        "arrow": prefix["endArrow"],
        "end_size": int(prefix["endSize"]),
    }
    primary = paths["Primary Path"]["strokeColor"]
    optional_primary = paths["Optional Primary Path"]
    optional_secondary = paths["Optional Secondary Path"]
    edges_gcp = {
        "traffic": {"stroke": primary, "width": base["width"], "dashed": False,
                    "arrow": base["arrow"], "end_size": base["end_size"]},
        "async": {"stroke": optional_primary["strokeColor"], "width": base["width"], "dashed": True,
                  "dash_pattern": optional_primary["dashPattern"],
                  "arrow": base["arrow"], "end_size": base["end_size"]},
        "peer": {"stroke": primary, "width": base["width"], "dashed": False,
                 "arrow": base["arrow"], "start_arrow": base["arrow"], "end_size": base["end_size"]},
        "dependency": {"stroke": optional_secondary["strokeColor"], "width": base["width"], "dashed": True,
                       "dash_pattern": optional_secondary["dashPattern"],
                       "arrow": base["arrow"], "end_size": base["end_size"]},
    }

    zones_block = function_block(source, "addGCP2ZonesPalette")
    palette = {
        fields["fillColor"]
        for args in call_arguments(zones_block, "this.createVertexTemplateEntry")
        for fields in [style_fields(eval_string_expr(args[0], {"s": ""}))]
        if "fillColor" in fields
    }
    # Project Zoneは複合テンプレートなので、ブロック全体からも塗りを拾う。
    for chunk in zones_block.split("fillColor=")[1:]:
        color = chunk.split(";", 1)[0]
        if color.startswith("#"):
            palette.add(color)
    return edges_gcp, palette


def diff(label: str, current: Any, upstream: Any, lines: list[str]) -> None:
    if isinstance(current, dict) and isinstance(upstream, dict):
        for key in sorted(set(current) | set(upstream)):
            if key == "note":
                continue
            diff(f"{label}.{key}", current.get(key), upstream.get(key), lines)
    elif current != upstream:
        lines.append(f"  {label}: {current!r} -> {upstream!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="style-tokens.jsonを上流の値へ更新する")
    parser.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS)
    args = parser.parse_args()

    tokens = json.loads(args.tokens.read_text(encoding="utf-8"))
    upstream_meta = tokens["upstream"]
    aws_groups = parse_aws_groups(fetch(upstream_meta["aws_sidebar"]))
    edges_gcp, gcp_palette = parse_gcp(fetch(upstream_meta["gcp_sidebar"]))

    lines: list[str] = []
    diff("providers.aws.groups", tokens["providers"]["aws"].get("groups", {}), aws_groups, lines)
    current_edges = {key: value for key, value in tokens.get("edges_gcp", {}).items() if key != "note"}
    diff("edges_gcp", current_edges, edges_gcp, lines)

    warnings: list[str] = []
    for key, value in tokens["providers"]["gcp"].items():
        if key.endswith("_fill") and value.upper() not in {color.upper() for color in gcp_palette}:
            warnings.append(
                f"  providers.gcp.{key}={value} が上流のZoneパレットに見当たらない。割り当てを見直すこと"
            )

    for warning in warnings:
        print("WARNING:" + warning)

    if not lines:
        print("in sync: style-tokens.json は上流と一致している")
        return 0

    print("drift detected:")
    print("\n".join(lines))

    if not args.write:
        print("\n--write で style-tokens.json を更新できる。更新後は self_test.py とプレビュー確認を行うこと")
        return 2

    tokens["providers"]["aws"]["groups"] = aws_groups
    note = tokens.get("edges_gcp", {}).get("note")
    tokens["edges_gcp"] = ({"note": note} if note else {}) | edges_gcp
    tokens["upstream"]["verified"] = datetime.date.today().isoformat()
    args.tokens.write_text(json.dumps(tokens, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {args.tokens}. 次に scripts/self_test.py を実行し、プレビューで見た目を確認すること")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
