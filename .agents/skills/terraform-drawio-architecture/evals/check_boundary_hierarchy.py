#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ADJACENT_BOUNDARIES = (
    ("resource-group", "japan-east"),
    ("japan-east", "vnet"),
    ("vnet", "bastion-subnet"),
)
STYLE_AXES = ("strokeColor", "strokeWidth", "dashPattern", "fillColor")
EXPECTED_STYLES = {
    "azure-cloud": {"strokeColor": "#0078D4", "strokeWidth": "3", "dashed": "0"},
    "resource-group": {"strokeColor": "#5F6368", "strokeWidth": "2.5", "dashPattern": "12 6"},
    "japan-east": {"strokeColor": "#9AA0A6", "strokeWidth": "2", "dashPattern": "8 6"},
    "vnet": {"strokeColor": "#0078D4", "strokeWidth": "1.5", "dashed": "0"},
    "bastion-subnet": {"strokeColor": "none", "fillColor": "#E6F2FA"},
}


def parse_style(style: str) -> dict[str, str]:
    return {
        key: value
        for part in style.split(";")
        if "=" in part
        for key, value in [part.split("=", 1)]
    }


def grade(drawio: Path) -> dict[str, object]:
    root = ET.parse(drawio).getroot()
    cells = {cell.get("id", ""): cell for cell in root.iter("mxCell")}
    missing = sorted(cell_id for cell_id in EXPECTED_STYLES if cell_id not in cells)
    styles = {
        cell_id: parse_style(cells[cell_id].get("style", ""))
        for cell_id in EXPECTED_STYLES
        if cell_id in cells
    }

    structure_passed = not missing
    structure_evidence = (
        "Target boundary cells are present and the XML parsed successfully."
        if structure_passed
        else f"Missing boundary cells: {', '.join(missing)}"
    )

    pair_evidence = []
    pair_results = []
    for outer, inner in ADJACENT_BOUNDARIES:
        if outer not in styles or inner not in styles:
            pair_results.append(False)
            pair_evidence.append(f"{outer} -> {inner}: missing cell")
            continue
        differences = [axis for axis in STYLE_AXES if styles[outer].get(axis) != styles[inner].get(axis)]
        pair_results.append(len(differences) >= 2)
        pair_evidence.append(f"{outer} -> {inner}: {len(differences)} axes ({', '.join(differences) or 'none'})")

    expected_mismatches = []
    for cell_id, expected in EXPECTED_STYLES.items():
        actual = styles.get(cell_id, {})
        for key, value in expected.items():
            if actual.get(key) != value:
                expected_mismatches.append(f"{cell_id}.{key}: expected {value}, got {actual.get(key)}")

    expectations = [
        {
            "text": "The output remains valid draw.io XML and preserves every target Azure boundary.",
            "passed": structure_passed,
            "evidence": structure_evidence,
        },
        {
            "text": "Every adjacent Resource Group, Region, VNet, and Subnet boundary differs on at least two visual axes.",
            "passed": all(pair_results),
            "evidence": "; ".join(pair_evidence),
        },
        {
            "text": "Azure boundary colors, widths, and dash patterns match the documented hierarchy tokens.",
            "passed": not expected_mismatches,
            "evidence": "All hierarchy tokens match." if not expected_mismatches else "; ".join(expected_mismatches),
        },
    ]
    passed = sum(1 for expectation in expectations if expectation["passed"])
    return {
        "expectations": expectations,
        "summary": {
            "passed": passed,
            "failed": len(expectations) - passed,
            "total": len(expectations),
            "pass_rate": passed / len(expectations),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("drawio", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = grade(args.drawio)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
