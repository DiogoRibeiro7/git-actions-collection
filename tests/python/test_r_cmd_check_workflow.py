"""Contracts for the public R CMD check reusable workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "r-cmd-check.yml"


def _load() -> dict[str, Any]:
    """Load the reusable R workflow."""
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _workflow_call(workflow: dict[str, Any]) -> dict[str, Any]:
    """Return the reusable workflow interface."""
    triggers = workflow.get("on") or workflow.get(True) or {}
    return triggers["workflow_call"]


def test_r_cmd_check_exposes_small_matrix_oriented_interface() -> None:
    workflow = _load()
    inputs = _workflow_call(workflow)["inputs"]

    assert workflow["permissions"] == {"contents": "read"}
    assert inputs["r-versions"]["default"] == '["release"]'
    assert inputs["os-matrix"]["default"] == '["ubuntu-latest"]'
    assert inputs["working-directory"]["default"] == "."
    assert inputs["check-args"]["default"] == '["--no-manual"]'
    assert inputs["error-on"]["default"] == "error"


def test_r_cmd_check_matrix_comes_from_inputs() -> None:
    workflow = _load()
    job = workflow["jobs"]["check"]

    assert job["strategy"]["fail-fast"] is False
    assert job["strategy"]["matrix"] == {
        "os": "${{ fromJSON(inputs.os-matrix) }}",
        "r": "${{ fromJSON(inputs.r-versions) }}",
    }
    assert job["runs-on"] == "${{ matrix.os }}"
    assert job["defaults"]["run"]["working-directory"] == "${{ inputs.working-directory }}"


def test_r_cmd_check_installs_dependencies_before_checking() -> None:
    steps = _load()["jobs"]["check"]["steps"]
    names = [step.get("name") for step in steps]

    assert names.index("Set up R") < names.index("Install check tooling")
    assert names.index("Install check tooling") < names.index("Validate package and inputs")
    assert names.index("Validate package and inputs") < names.index("Install package dependencies")
    assert names.index("Install package dependencies") < names.index("Run R CMD check")

    check = next(step for step in steps if step.get("name") == "Run R CMD check")
    assert "rcmdcheck::rcmdcheck" in check["run"]
    assert "error_on = Sys.getenv(\"ERROR_ON\")" in check["run"]
    assert "jsonlite::fromJSON(Sys.getenv(\"CHECK_ARGS\"))" in check["run"]


def test_r_cmd_check_fails_when_description_or_policy_input_is_invalid() -> None:
    validate = next(
        step
        for step in _load()["jobs"]["check"]["steps"]
        if step.get("name") == "Validate package and inputs"
    )

    assert "DESCRIPTION not found" in validate["run"]
    assert "error-on must be one of: error, warning, note" in validate["run"]
    assert "check-args must be a JSON array of strings" in validate["run"]
