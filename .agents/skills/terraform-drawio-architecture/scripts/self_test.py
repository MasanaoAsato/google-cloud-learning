#!/usr/bin/env python3

"""Regression tests for the guarantees that make a generated diagram readable.

Each case here exists because its absence produced a defect a reader noticed:
labels drawn across boundaries, Japanese broken mid-word, cramped or hollow
frames, and nodes without icons.
"""

from __future__ import annotations

import copy
import tempfile
from pathlib import Path

import drawio_styles
import export_svg
import layout as layout_engine
import preview
import text_layout
from build_drawio import DEFAULT_ICONS, DEFAULT_TEMPLATE, DEFAULT_TOKENS, build, load_tokens
from icon_catalog import IconCatalog
from inspect_drawio import graph_inventory, read_graph_model, read_mxfile
from validate_artifacts import validate_drawio, validate_svg
from validate_diagram_spec import validate


def evidence(note: str) -> list[dict[str, object]]:
    return [{"source": "main.tf", "line": 1, "note": note}]


def check_azure_boundary_styles(tokens: dict[str, object]) -> None:
    """Azureは専用境界シェイプが無いので、汎用規則（外側ほど太い、subnetは塗りのみ）で描く。"""
    expected_fragments = {
        "cloud": ("strokeColor=#0078D4", "strokeWidth=3", "dashed=0"),
        "resource-group": ("strokeColor=#5F6368", "strokeWidth=2.5", "dashPattern=12 6"),
        "region": ("strokeColor=#9AA0A6", "strokeWidth=2", "dashPattern=8 6"),
        "network": ("strokeColor=#0078D4", "strokeWidth=1.5", "dashed=0"),
        "subnet": ("strokeColor=none", "fillColor=#E6F2FA"),
    }
    styles = {
        kind: drawio_styles.container_style(tokens, {"provider": "azure", "kind": kind})
        for kind in expected_fragments
    }
    for kind, fragments in expected_fragments.items():
        assert all(fragment in styles[kind] for fragment in fragments), styles[kind]

    assert len(set(styles.values())) == len(styles)

    canvas = preview.Canvas(100, 100)
    canvas.rect((10, 10, 80, 80), "#FFFFFF", "#505050", dashed=True, dash_pattern="2 4")
    assert 'stroke-dasharray="2 4"' in canvas.render()


def check_native_boundary_shapes(tokens: dict[str, object]) -> None:
    """境界を意味する専用シェイプがあるクラウドでは必ずそれを使う。

    AWSはDraw.io公式のGroups（grIcon付き）、GCPは公式Zones（囲い線なしの塗り）。
    上流由来の色はsync_upstream.pyが更新するので、リテラルではなくトークンと
    生成styleの整合を検査する。
    """
    groups = tokens["providers"]["aws"]["groups"]
    aws = lambda item: drawio_styles.container_style(tokens, {"provider": "aws", **item})

    for kind, item in (
        ("cloud", {"kind": "cloud"}),
        ("region", {"kind": "region"}),
        ("network", {"kind": "network"}),
        ("external", {"kind": "external"}),
    ):
        style = aws(item)
        group = groups[kind]
        assert "shape=mxgraph.aws4.group" in style, style
        assert f"grIcon=mxgraph.aws4.{group['icon']}" in style, style
        assert f"strokeColor={group['stroke']}" in style, style
        assert f"dashed={1 if group['dashed'] else 0}" in style, style

    zone = aws({"kind": "zone"})
    assert "grIcon" not in zone and f"strokeColor={groups['zone']['stroke']}" in zone and "dashed=1" in zone, zone

    for key, item in (
        ("public_subnet", {"kind": "subnet", "variant": "public"}),
        ("private_subnet", {"kind": "subnet"}),
    ):
        style = aws(item)
        group = groups[key]
        assert "grStroke=0" in style, style
        assert f"fillColor={group['fill']}" in style, style
        assert f"strokeColor={group['stroke']}" in style, style

    # grIcon付きの境界は境界名をアイコンの右へ逃がす。
    assert drawio_styles.container_label_indent(aws({"kind": "cloud"})) > 0
    assert drawio_styles.container_label_indent(zone) == 0

    # 可読性のためのgroup_overridesが境界名の色へ効いている。
    override_font = tokens["providers"]["aws"]["group_overrides"]["network"]["font"]
    assert drawio_styles.container_label_color(tokens, {"provider": "aws", "kind": "network"}) == override_font

    gcp_fill = tokens["providers"]["gcp"]["network_fill"]
    gcp_network = drawio_styles.container_style(tokens, {"provider": "gcp", "kind": "network"})
    assert "strokeColor=none" in gcp_network and f"fillColor={gcp_fill}" in gcp_network, gcp_network
    assert "arcSize=2" in gcp_network, gcp_network


def check_edge_styles(tokens: dict[str, object]) -> None:
    """線は6種別。GCP図では公式Pathsの色と矢頭へ置き換わる。"""
    edges = tokens["edges"]
    sync = drawio_styles.edge_style(tokens, {"kind": "traffic", "status": "confirmed"})
    assert f"strokeColor={edges['traffic']['stroke']}" in sync and "dashed=0" in sync, sync
    peer = drawio_styles.edge_style(tokens, {"kind": "peer", "status": "confirmed"})
    assert f"startArrow={edges['peer']['start_arrow']}" in peer and "startFill=1" in peer, peer
    dependency = drawio_styles.edge_style(tokens, {"kind": "dependency", "status": "confirmed"})
    assert f"dashPattern={edges['dependency']['dash_pattern']}" in dependency, dependency
    special = drawio_styles.edge_style(tokens, {"kind": "special", "status": "confirmed"})
    assert f"strokeColor={edges['special']['stroke']}" in special and "strokeWidth=3" in special, special

    gcp = tokens["edges_gcp"]
    gcp_sync = drawio_styles.edge_style(tokens, {"kind": "traffic", "status": "confirmed"}, "gcp")
    assert f"strokeColor={gcp['traffic']['stroke']}" in gcp_sync, gcp_sync
    assert f"endArrow={gcp['traffic']['arrow']}" in gcp_sync, gcp_sync
    # controlはGCP公式Pathsに対応が無いので共通規則のまま。
    gcp_control = drawio_styles.edge_style(tokens, {"kind": "control", "status": "confirmed"}, "gcp")
    assert f"strokeColor={edges['control']['stroke']}" in gcp_control, gcp_control


def sample_spec() -> dict[str, object]:
    return {
        "schema_version": 1,
        "title": "Cloud Run 公開構成",
        "subtitle": "Terraform ルート: .",
        "provider": "gcp",
        "source_roots": ["."],
        "canvas": {"width": 960, "height": 570},
        "containers": [
            {
                "id": "internet",
                "kind": "external",
                "label": "インターネット",
                "provider": "neutral",
                "parent": None,
                "status": "derived",
                "geometry": {"x": 40, "y": 120, "width": 340, "height": 190},
                "evidence": evidence("external endpoint"),
            },
            {
                "id": "cloud",
                "kind": "cloud",
                "label": "Google Cloud",
                "provider": "gcp",
                "parent": None,
                "status": "confirmed",
                "geometry": {"x": 420, "y": 120, "width": 460, "height": 350},
                "evidence": evidence("provider"),
            },
            {
                "id": "region",
                "kind": "region",
                "label": "asia-northeast1（リージョン）",
                "provider": "gcp",
                "parent": "cloud",
                "status": "confirmed",
                "geometry": {"x": 30, "y": 50, "width": 400, "height": 200},
                "evidence": evidence("location"),
            },
        ],
        "nodes": [
            {
                "id": "user",
                "provider": "neutral",
                "service": "利用者",
                "role": "インターネットからの参照元",
                "label": "利用者（ブラウザ）",
                "container": "internet",
                "status": "derived",
                "geometry": {"x": 30, "y": 50, "width": 280, "height": 100},
                "evidence": evidence("public endpoint"),
            },
            {
                "id": "run",
                "terraform_address": "module.run.google_cloud_run_v2_service.main",
                "provider": "gcp",
                "service": "Cloud Run",
                "role": "コンテナ実行",
                "label": "Cloud Run",
                "container": "region",
                "status": "confirmed",
                "geometry": {"x": 30, "y": 50, "width": 280, "height": 100},
                "evidence": evidence("Cloud Run service"),
            },
        ],
        "edges": [
            {
                "id": "traffic",
                "from": "user",
                "to": "run",
                "kind": "traffic",
                "label": "HTTPS",
                "status": "confirmed",
                "evidence": evidence("ingress"),
            }
        ],
        "legend": {"show": True, "x": 40, "y": 480, "width": 240},
        "omissions": [],
        "unresolved": [],
    }


def check_line_breaking() -> None:
    """Japanese must not break inside a katakana word or between okurigana."""
    lines = text_layout.wrap("ターゲット HTTPS プロキシ", 150, 13, bold=True)
    assert all(not line.endswith("プロキ") for line in lines), lines
    assert any("プロキシ" in line for line in lines), lines

    lines = text_layout.wrap("Serverless NEG を束ねる", 150, 11)
    assert any("束ねる" in line for line in lines), lines

    lines = text_layout.wrap("転送ルール・グローバル IP", 150, 13, bold=True)
    widest = max(text_layout.measure(line, 13, True) for line in lines)
    narrowest = min(text_layout.measure(line, 13, True) for line in lines)
    assert widest - narrowest < 60, f"lines are unbalanced: {lines}"

    for line in text_layout.wrap("日本国外からのアクセスを拒否する", 120, 11):
        assert not line.startswith("。"), line


def check_icons() -> None:
    """The icon policy: stencils first, sidebar images for the gaps, then KeyError."""
    catalog = IconCatalog.load(DEFAULT_ICONS)
    style, source = catalog.resolve("Cloud Run", "gcp")
    assert "shape=mxgraph.gcp2.cloud_run" in style, source
    for service in ("Artifact Registry", "Eventarc", "Secret Manager"):
        style, source = catalog.resolve(service, "gcp")
        assert "shape=image" in style, (service, source)
        assert "sidebar image" in source, (service, source)
    for subject in ("利用者", "インターネット", "オンプレミス", "ブラウザ"):
        style, source = catalog.resolve(subject)
        assert "shape=mxgraph." in style, (subject, source)
    try:
        catalog.resolve("Totally Invented Service")
    except KeyError:
        pass
    else:  # pragma: no cover
        raise AssertionError("unknown services must not resolve to an icon")


def check_missing_stencil_instructions() -> None:
    """Azure image paths must be directly usable by the maintenance command."""
    azure_error = str(
        preview._missing_stencil(
            "image", "img/lib/azure2/containers/Container_Registries.svg"
        )
    )
    command_target = azure_error.split("render_stencils.py ", 1)[1].split("' once", 1)[0]
    assert command_target == "azure2/containers/Container_Registries.svg", azure_error

    gcp_error = str(preview._missing_stencil("stencil", "mxgraph.gcp2.users"))
    assert "gcp2/users" in gcp_error, gcp_error


def grid_spec() -> dict[str, object]:
    """The same architecture as ``sample_spec`` but with grid cells, no geometry."""
    spec = copy.deepcopy(sample_spec())
    del spec["canvas"]
    del spec["legend"]
    spec["containers"][0]["grid"] = {"row": 0, "col": 0}
    spec["containers"][1]["grid"] = {"row": 0, "col": 1}
    for item in spec["containers"] + spec["nodes"]:
        item.pop("geometry", None)
    spec["nodes"].append(
        {
            "id": "lb",
            "provider": "gcp",
            "service": "cloud load balancing",
            "role": "HTTPS終端",
            "label": "外部アプリケーション LB",
            "container": "region",
            "grid": {"row": 0, "col": 0},
            "status": "confirmed",
            "evidence": evidence("forwarding rule"),
        }
    )
    spec["nodes"][1]["grid"] = {"row": 1, "col": 0}
    return spec


def check_auto_layout(tokens: dict[str, object]) -> None:
    """Grid-only specs must satisfy the spacing contract by construction."""
    # A fully hand-placed spec passes through untouched: hand-tuning survives.
    pinned = sample_spec()
    assert layout_engine.resolve(pinned, tokens) is pinned

    resolved = layout_engine.resolve(grid_spec(), tokens)
    errors, warnings = validate(resolved)
    assert not errors, errors
    assert not warnings, warnings

    by_id = {item["id"]: item for item in resolved["containers"] + resolved["nodes"]}
    # Same column, same width: the vertical edge between them runs straight.
    lb, run = by_id["lb"]["geometry"], by_id["run"]["geometry"]
    assert lb["width"] == run["width"] and lb["x"] == run["x"], (lb, run)
    # The canvas and the legend are derived, and the legend sits inside the canvas.
    legend = resolved["legend"]
    assert legend["y"] + 50 < resolved["canvas"]["height"], (legend, resolved["canvas"])

    # A pinned container too small for its auto-laid children is a hard error,
    # not a silent overflow.
    cramped = grid_spec()
    cramped["containers"][2]["geometry"] = {"x": 30, "y": 50, "width": 200, "height": 100}
    del cramped["containers"][2]["parent"]
    cramped["containers"][2]["parent"] = "cloud"
    try:
        layout_engine.resolve(cramped, tokens)
    except ValueError as exc:
        assert "auto-laid children" in str(exc), exc
    else:  # pragma: no cover
        raise AssertionError("cramped pinned container must fail layout")


def check_flow_direction(tokens: dict[str, object]) -> None:
    """Main paths that double back against the declared flow are flagged."""
    reversed_spec = grid_spec()
    edge = reversed_spec["edges"][0]
    edge["from"], edge["to"] = edge["to"], edge["from"]  # run -> user: right to left
    resolved = layout_engine.resolve(reversed_spec, tokens)
    _, warnings = validate(resolved)
    assert any("against the horizontal flow" in w for w in warnings), warnings

    # Management paths may run wherever they need to.
    control_spec = grid_spec()
    control_edge = control_spec["edges"][0]
    control_edge["from"], control_edge["to"] = control_edge["to"], control_edge["from"]
    control_edge["kind"] = "control"
    _, warnings = validate(layout_engine.resolve(control_spec, tokens))
    assert not any("flow" in w for w in warnings), warnings

    # A diagram may declare itself vertical; a downward main path then passes.
    vertical = grid_spec()
    vertical["flow"] = "vertical"
    _, warnings = validate(layout_engine.resolve(vertical, tokens))
    assert not any("flow" in w for w in warnings), warnings

    invalid = grid_spec()
    invalid["flow"] = "diagonal"
    errors, _ = validate(layout_engine.resolve(invalid, tokens))
    assert any("flow must be" in e for e in errors), errors


def check_padding_rules(spec: dict[str, object]) -> None:
    """Cramped frames fail; hollow frames warn."""
    cramped = copy.deepcopy(spec)
    cramped["nodes"][1]["geometry"] = {"x": 30, "y": 10, "width": 280, "height": 100}
    errors, _ = validate(cramped)
    assert any("padding on the top" in error for error in errors), errors

    hollow = copy.deepcopy(spec)
    hollow["containers"][0]["geometry"] = {"x": 40, "y": 120, "width": 340, "height": 400}
    hollow["legend"] = {"show": True, "x": 680, "y": 490, "width": 240}
    _, warnings = validate(hollow)
    assert any("unused space" in warning for warning in warnings), warnings

    tight = copy.deepcopy(spec)
    tight["nodes"][1]["label"] = "非常に長いサービス表示名をカードへ詰め込む例"
    tight["nodes"][1]["role"] = "説明も限界まで詰めて折り返しを溢れさせる例"
    tight["nodes"][1]["geometry"] = {"x": 30, "y": 50, "width": 260, "height": 96}
    errors, _ = validate(tight)
    assert any("offers" in error for error in errors), errors

    close = copy.deepcopy(spec)
    close["containers"][0]["geometry"] = {"x": 40, "y": 120, "width": 370, "height": 190}
    errors, _ = validate(close)
    assert any("apart" in error for error in errors), errors


def check_placeholder_fallback(tokens: dict, catalog: IconCatalog) -> None:
    """A service without any icon is a warning and builds as a plain marked box."""
    spec = sample_spec()
    spec["nodes"][1]["service"] = "まだ存在しない新サービス"
    errors, warnings = validate(spec)
    assert not errors, errors
    assert any("plain box" in warning for warning in warnings), warnings

    tree = build(spec, tokens, DEFAULT_TEMPLATE, catalog)
    with tempfile.TemporaryDirectory(prefix="terraform-drawio-self-test-") as temp:
        drawio = Path(temp) / "fallback.drawio"
        tree.write(drawio, encoding="utf-8", xml_declaration=True)
        cells = {
            cell["id"]: cell
            for cell in graph_inventory(read_graph_model(read_mxfile(drawio)))["cells"]
        }
        assert "placeholderIcon=1" in cells["run__icon"]["style"], cells["run__icon"]
        artifact_errors, _, _ = validate_drawio(spec, drawio)
        assert not artifact_errors, artifact_errors
        exported = Path(temp) / "fallback.svg"
        export_svg.export(drawio, exported, DEFAULT_TOKENS, DEFAULT_ICONS)


def main() -> int:
    check_line_breaking()
    check_icons()
    check_missing_stencil_instructions()

    spec = sample_spec()
    errors, warnings = validate(spec)
    assert not errors, errors
    assert not warnings, warnings

    check_padding_rules(spec)

    tokens = load_tokens(DEFAULT_TOKENS)
    check_auto_layout(tokens)
    check_flow_direction(tokens)
    check_azure_boundary_styles(tokens)
    check_native_boundary_shapes(tokens)
    check_edge_styles(tokens)
    catalog = IconCatalog.load(DEFAULT_ICONS)
    check_placeholder_fallback(tokens, catalog)
    with tempfile.TemporaryDirectory(prefix="terraform-drawio-self-test-") as temp:
        drawio = Path(temp) / "architecture.drawio"
        tree = build(spec, tokens, DEFAULT_TEMPLATE, catalog)
        tree.write(drawio, encoding="utf-8", xml_declaration=True)

        artifact_errors, _, _ = validate_drawio(spec, drawio)
        assert not artifact_errors, artifact_errors

        model = read_graph_model(read_mxfile(drawio))
        inventory = graph_inventory(model)
        cells = {cell["id"]: cell for cell in inventory["cells"]}

        # Draw.io crops exports to cell bounds. A white full-canvas cell preserves
        # the layout margin and makes the editor/export background deterministic.
        assert model.attrib.get("background") == "#FFFFFF"
        canvas_background = cells["meta-canvas-background"]
        assert canvas_background["parent"] == "layer-background"
        assert "fillColor=#FFFFFF" in canvas_background["style"]
        assert "strokeColor=none" in canvas_background["style"]
        assert "locked=1" in canvas_background["style"]
        assert canvas_background["geometry"]["x"] == 0
        assert canvas_background["geometry"]["y"] == 0
        assert canvas_background["geometry"]["width"] == spec["canvas"]["width"]
        assert canvas_background["geometry"]["height"] == spec["canvas"]["height"]

        assert cells["run"]["terraform_address"] == "module.run.google_cloud_run_v2_service.main"
        assert "module.run" not in cells["run"]["value"]
        assert "module.run" not in cells["run__label"]["value"]
        assert "shape=mxgraph.gcp2.cloud_run" in cells["run__icon"]["style"]
        assert "shape=mxgraph.gcp2.users" in cells["user__icon"]["style"]

        # Boundary names live in their own cell. GCP boundaries use the official
        # zone treatment: borderless fill with the same 2px micro-rounding as cards.
        assert cells["cloud"]["value"] == ""
        assert "strokeColor=none" in cells["cloud"]["style"]
        assert "arcSize=2" in cells["cloud"]["style"]
        assert "fillColor=#F6F6F6" in cells["cloud"]["style"]
        assert "Google Cloud" in cells["cloud__label"]["value"]
        assert cells["cloud__label"]["geometry"]["y"] >= 10

        # Lines are fixed here so the browser cannot re-wrap them.
        assert "white-space:nowrap" in cells["run__label"]["value"]

        drawn = preview.build_svg(drawio, tokens)
        assert drawn.startswith("<svg"), drawn[:40]
        assert "Cloud Run" in drawn

        # The exporter draws every icon for real (stencils via pre-renderings),
        # embeds the editable XML, and the result matches the .drawio.
        exported = Path(temp) / "architecture.svg"
        export_svg.export(drawio, exported, DEFAULT_TOKENS, DEFAULT_ICONS)
        svg_text = exported.read_text(encoding="utf-8")
        assert "content=" in svg_text.split("\n", 1)[0], "editable XML must be embedded"
        assert svg_text.count("data:image/svg+xml;base64") >= 2, "icons must render as images"
        assert "#E8F0FE" not in svg_text, "an export must not contain stencil placeholders"
        required_ids = {
            item["id"]
            for field in ("containers", "nodes", "edges")
            for item in spec.get(field, [])
        }
        svg_errors, _ = validate_svg(exported, inventory, required_ids)
        assert not svg_errors, svg_errors

    print(
        "self-test passed: icon for every subject, boundary labels off the border, "
        "Japanese breaks at word boundaries, padding contract enforced, export bounds preserved, "
        "preview renders, SVG export embeds the diagram with every icon drawn"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
