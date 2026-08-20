#!/usr/bin/env python3

"""Draw.io style strings for boundaries, cards, text and edges.

Keeping the style strings here means a colour, a corner radius or a font size is
changed in one obvious place, and ``build_drawio.py`` stays about the structure of
the diagram. Values come from ``assets/style-tokens.json``; this module only turns
them into the ``key=value;`` form Draw.io expects.
"""

from __future__ import annotations

from typing import Any

BOUNDARY_KINDS = {"cloud", "organization", "account", "subscription", "project"}

# 外側の領域ほど太い。主要な入れ子チェーン（cloud > account/project > region >
# zone/network > subnet）で線幅が単調に細くなるように選ぶ。subnetは枠線を持たず
# 塗りだけで示すので、この表の幅はunresolved表示などの補助にしか使わない。
BOUNDARY_BORDER_PROFILES = {
    "cloud": (3.0, None),
    "organization": (2.5, "12 6"),
    "account": (2.5, "12 6"),
    "subscription": (2.5, "12 6"),
    "project": (2.5, "12 6"),
    "resource-group": (2.5, "12 6"),
    "region": (2.0, "8 6"),
    "zone": (1.5, "8 6"),
    "network": (1.5, None),
    "subnet": (1.0, None),
    "cluster": (1.25, "6 4"),
    "namespace": (1.0, "3 4"),
}

# Draw.io公式「AWS / Groups」パレットの値は`style-tokens.json`の`providers.aws.groups`
# にあり、`maintenance/sync_upstream.py`が上流（jgraph/drawio Sidebar-AWS4.js）と同期する。
# grIconの綴りが違うと角のアイコンは黙って消えるので、値を手で編集しない。
# Availability Zoneは公式でもアイコン無しの破線矩形である。
_AWS_POINTS = (
    "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],"
    "[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]]"
)

# Draw.io公式「GCP / Zones」の塗り（Sidebar-GCP2.js）。囲い線なし・角丸2pxの
# 塗り領域が公式の境界表現なので、GCPだけは直角ルールの例外になる。
_GCP_ZONE_KEYS = {
    "cloud": "cloud_fill",
    "organization": "project_fill",
    "folder": "project_fill",
    "project": "project_fill",
    "region": "region_fill",
    "zone": "zone_fill",
    "network": "network_fill",
    "subnet": "subnet_fill",
    "cluster": "cluster_fill",
    "namespace": "namespace_fill",
}

_CONTAINER_BEHAVIOUR = [
    "container=1",
    "collapsible=0",
    "recursiveResize=0",
    "pointerEvents=0",
    "whiteSpace=wrap",
    "html=1",
    "verticalAlign=top",
    "align=left",
    "sketch=0",
]


def provider_palette(tokens: dict[str, Any], provider: str) -> dict[str, str]:
    providers = tokens["providers"]
    return providers.get(provider, providers["neutral"])


def _aws_group_def(tokens: dict[str, Any], item: dict[str, Any]) -> dict[str, Any] | None:
    aws = tokens["providers"]["aws"]
    kind = item.get("kind", "group")
    if kind == "subnet":
        kind = "public_subnet" if item.get("variant", "").lower() == "public" else "private_subnet"
    group = aws.get("groups", {}).get(kind)
    if group is None:
        return None
    override = aws.get("group_overrides", {}).get(kind)
    if isinstance(override, dict):
        group = {**group, **override}
    return group


def _finish(parts: list[str], item: dict[str, Any]) -> str:
    if item.get("status") == "unresolved":
        parts.extend(["strokeColor=#F29900", "strokeWidth=2", "dashed=1", "dashPattern=6 4"])
    return ";".join(parts) + ";"


def container_style(tokens: dict[str, Any], item: dict[str, Any]) -> str:
    provider = item.get("provider", "neutral")
    kind = item.get("kind", "group")
    variant = item.get("variant", "").lower()
    stroke_width, dash_pattern = BOUNDARY_BORDER_PROFILES.get(kind, (1.5, None))

    # 大前提: 境界を意味する専用シェイプがあるクラウドでは必ずそれを使う。
    # AWSはGroups、GCPはZonesが該当し、Azureには存在しないため汎用規則で描く。
    group = _aws_group_def(tokens, item) if provider == "aws" else None
    if group is not None:
        parts = list(_CONTAINER_BEHAVIOUR)
        parts.extend([_AWS_POINTS, "outlineConnect=0", "gradientColor=none", "rounded=0"])
        if group.get("icon"):
            parts.extend(["shape=mxgraph.aws4.group", f"grIcon=mxgraph.aws4.{group['icon']}"])
        if group.get("borderless"):
            # 公式のサブネット表現。grStroke=0で枠線を消し、塗りだけで領域を示す。
            parts.extend(["grStroke=0", f"strokeColor={group['stroke']}", f"fillColor={group['fill']}", "dashed=0"])
        else:
            parts.extend(
                [
                    f"strokeColor={group['stroke']}",
                    "fillColor=none",
                    f"strokeWidth={stroke_width:g}",
                    f"dashed={1 if group.get('dashed') else 0}",
                ]
            )
        return _finish(parts, item)

    if provider == "gcp" and kind in _GCP_ZONE_KEYS:
        palette = provider_palette(tokens, provider)
        fill = palette[_GCP_ZONE_KEYS[kind]]
        parts = list(_CONTAINER_BEHAVIOUR)
        # 公式Zoneスタイル。カードと同じ2pxの微小な角丸で、枠線は持たない。
        parts.extend(
            [
                "rounded=1",
                "absoluteArcSize=1",
                "arcSize=2",
                "gradientColor=none",
                "shadow=0",
                "strokeColor=none",
                f"fillColor={fill}",
                "dashed=0",
            ]
        )
        return _finish(parts, item)

    stroke, fill, dashed = _fallback_colors(tokens, item, provider, kind, variant)
    parts = list(_CONTAINER_BEHAVIOUR)
    # 汎用規則の境界は直角にする。角丸の入れ子は装飾に見え、階層を追いにくくする。
    parts.append("rounded=0")
    if stroke == "none":
        # subnetは囲い線を持たず、塗りだけで領域を示す。
        parts.extend(["strokeColor=none", f"fillColor={fill}", "dashed=0"])
    else:
        parts.extend(
            [
                f"strokeColor={stroke}",
                f"fillColor={fill}",
                f"strokeWidth={stroke_width:g}",
                f"dashed={1 if dashed else 0}",
            ]
        )
        if dashed and dash_pattern:
            parts.append(f"dashPattern={dash_pattern}")
    return _finish(parts, item)


def _fallback_colors(
    tokens: dict[str, Any],
    item: dict[str, Any],
    provider: str,
    kind: str,
    variant: str,
) -> tuple[str, str, bool]:
    """専用シェイプが無い場合の汎用境界規則。

    クラウドは濃色の実線、リージョンとゾーンは青系の破線、ネットワークは実線、
    サブネットは囲い線なしの塗りにする。親子関係にあるネットワークとサブネットは
    同系色でまとめ、public/privateの違いは塗りで分ける。
    """
    palette = provider_palette(tokens, provider)
    neutral = tokens["providers"]["neutral"]

    if provider == "azure":
        if kind == "cloud":
            return palette["cloud_stroke"], palette["cloud_fill"], False
        if kind == "subscription":
            return palette["subscription_stroke"], palette["subscription_fill"], True
        if kind == "resource-group":
            return palette["resource_group_stroke"], palette["resource_group_fill"], True
        if kind == "region":
            return palette["region_stroke"], palette["region_fill"], True
        if kind == "network":
            return palette["network_stroke"], palette["network_fill"], False
        if kind == "subnet":
            return "none", palette["subnet_fill"], False
    else:
        if kind == "cloud":
            return neutral["cloud_stroke"], neutral["cloud_fill"], False
        if kind in {"region", "zone"}:
            return neutral["region_stroke"], "none", True
        if kind == "network":
            return neutral["network_stroke"], "none", False
        if kind == "subnet":
            fill = neutral["public_subnet_fill"] if variant == "public" else neutral["private_subnet_fill"]
            return "none", fill, False
        if provider == "gcp" and kind == "group":
            return palette["group_stroke"], palette["group_fill"], False

    if kind == "external":
        return neutral["stroke"], neutral["fill"], True
    return neutral["stroke"], neutral["fill"], False


def container_label_color(tokens: dict[str, Any], item: dict[str, Any]) -> str | None:
    """境界名の文字色。専用シェイプの公式配色に合わせ、無ければ既定の文字色を使う。"""
    if item.get("status") == "unresolved":
        return "#F29900"
    provider = item.get("provider", "neutral")
    if provider == "aws":
        group = _aws_group_def(tokens, item)
        if group is not None:
            return group["font"]
    if provider == "gcp" and item.get("kind") in _GCP_ZONE_KEYS:
        return tokens["typography"]["muted_text_color"]
    return None


def container_label_indent(style: str) -> float:
    """grIcon付きの境界は左上にアイコンが乗るので、境界名をその右へ逃がす。"""
    return 28.0 if "grIcon=" in style else 0.0


def text_style(
    tokens: dict[str, Any],
    size: float,
    *,
    bold: bool = False,
    color: str | None = None,
    align: str = "left",
    vertical: str = "middle",
) -> str:
    typography = tokens["typography"]
    parts = [
        "text",
        "html=1",
        "strokeColor=none",
        "fillColor=none",
        "whiteSpace=wrap",
        "overflow=visible",
        f"align={align}",
        f"verticalAlign={vertical}",
        "spacing=0",
        "spacingLeft=0",
        "spacingTop=0",
        f"fontFamily={typography['font_family']}",
        f"fontSize={size:g}",
        f"fontColor={color or typography['text_color']}",
    ]
    if bold:
        parts.append("fontStyle=1")
    return ";".join(parts) + ";"


def card_style(tokens: dict[str, Any], item: dict[str, Any]) -> str:
    card = tokens["card"]
    fill = card["fill"] if item.get("provider") in {"aws", "azure", "gcp"} else tokens["providers"]["neutral"]["fill"]
    parts = [
        "container=1",
        "collapsible=0",
        "recursiveResize=0",
        "rounded=1",
        "absoluteArcSize=1",
        f"arcSize={card['corner_radius']}",
        "whiteSpace=wrap",
        "html=1",
        f"fillColor={fill}",
        f"strokeColor={card['stroke']}",
        f"strokeWidth={card['stroke_width']}",
        f"shadow={1 if card.get('shadow') else 0}",
        "sketch=0",
    ]
    if item.get("status") == "unresolved":
        parts.extend(["strokeColor=#F29900", "strokeWidth=2", "dashed=1"])
    return ";".join(parts) + ";"


def placeholder_icon_style() -> str:
    """Last tier of the icon policy: a plain dashed box marks a missing icon.

    ``placeholderIcon=1`` is the machine-readable marker the artifact validator
    accepts in place of a stencil or image icon.
    """
    return (
        "placeholderIcon=1;rounded=0;html=1;fillColor=#FFFFFF;"
        "strokeColor=#5F6368;strokeWidth=1;dashed=1;dashPattern=2 2;sketch=0;"
    )


def edge_token(tokens: dict[str, Any], item: dict[str, Any], provider: str | None = None) -> dict[str, Any]:
    """種別と対象クラウドから線の見た目を解決する。

    GCPには公式の「GCP / Paths」があるので、該当する種別だけ`edges_gcp`の
    定義へ置き換える。他クラウドと共通種別（control、special、unresolved）は
    共通の`edges`定義を使う。
    """
    key = "unresolved" if item.get("status") == "unresolved" else item.get("kind", "dependency")
    edge = tokens["edges"].get(key, tokens["edges"]["dependency"])
    if provider and key != "unresolved":
        override = tokens.get(f"edges_{provider}", {}).get(key)
        if isinstance(override, dict):
            edge = override
    return edge


def edge_style(tokens: dict[str, Any], item: dict[str, Any], provider: str | None = None) -> str:
    edge = edge_token(tokens, item, provider)
    parts = [
        "edgeStyle=orthogonalEdgeStyle",
        "rounded=0",
        "orthogonalLoop=1",
        "jettySize=auto",
        "html=1",
        f"strokeColor={edge['stroke']}",
        f"strokeWidth={edge['width']}",
        f"dashed={1 if edge['dashed'] else 0}",
        f"endArrow={edge['arrow']}",
        "endFill=1",
        f"fontFamily={tokens['typography']['font_family']}",
        "fontSize=11",
        "labelBackgroundColor=#FFFFFF",
    ]
    if edge.get("dashed") and edge.get("dash_pattern"):
        parts.append(f"dashPattern={edge['dash_pattern']}")
    # 双方向はレプリケーションやピアリングのように対等な関係を確認できた場合だけ使う。
    start_arrow = edge.get("start_arrow")
    if item.get("bidirectional") and not start_arrow:
        start_arrow = edge["arrow"]
    if start_arrow:
        parts.extend([f"startArrow={start_arrow}", "startFill=1"])
    if edge.get("end_size"):
        parts.extend([f"endSize={edge['end_size']}", f"startSize={edge['end_size']}"])
    return ";".join(parts) + ";"
