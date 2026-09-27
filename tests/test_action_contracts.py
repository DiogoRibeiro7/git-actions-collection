"""Public wiring contracts that do not require executing external actions."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_secret_scan_forwards_arguments_to_the_gitleaks_cli():
    """gitleaks-action declares no inputs, so `with: args` used to be dropped; the
    action now installs the CLI and hands `args` to its own scan script."""
    document = yaml.safe_load((ROOT / ".github/actions/secret-scan/action.yml").read_text())
    install, scan = document["runs"]["steps"]

    assert document["inputs"]["args"]["default"] == "--no-git -v"
    assert "scripts/secret-scan/install.sh" in install["run"]
    assert "scripts/secret-scan/scan.sh" in scan["run"]
    assert scan["env"]["INPUT_ARGS"] == "${{ inputs.args }}"
    assert not any("uses" in step for step in document["runs"]["steps"])


def test_dependency_update_exposes_report_from_the_executing_step():
    document = yaml.safe_load(
        (ROOT / ".github/actions/smart-dependency-update/action.yml").read_text()
    )
    value = document["outputs"]["report"]["value"]
    assert value == "${{ steps.run.outputs.report }}"
    producer = next(step for step in document["runs"]["steps"] if step.get("id") == "run")
    assert "scripts/actions/smart-dependency-update/run.sh" in producer["run"]
