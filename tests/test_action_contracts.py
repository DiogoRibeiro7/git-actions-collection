"""Public wiring contracts that do not require executing external actions."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_secret_scan_forwards_arguments_to_gitleaks():
    document = yaml.safe_load((ROOT / ".github/actions/secret-scan/action.yml").read_text())
    scanner = next(
        step
        for step in document["runs"]["steps"]
        if step.get("uses", "").startswith("gitleaks/gitleaks-action@")
    )
    assert document["inputs"]["args"]["default"] == "--no-git -v"
    assert scanner["with"]["args"] == "${{ inputs.args }}"


def test_dependency_update_exposes_report_from_the_executing_step():
    document = yaml.safe_load(
        (ROOT / ".github/actions/smart-dependency-update/action.yml").read_text()
    )
    value = document["outputs"]["report"]["value"]
    assert value == "${{ steps.run.outputs.report }}"
    producer = next(step for step in document["runs"]["steps"] if step.get("id") == "run")
    assert "scripts/actions/smart-dependency-update/run.sh" in producer["run"]
