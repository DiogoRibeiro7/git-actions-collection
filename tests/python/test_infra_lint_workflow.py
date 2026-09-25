"""infra-lint never failed and never linted.

Both linters ended in `|| true`, TFLint rejected the positional path it was given
(dropped in v0.47), and cfn-lint was pointed at a directory, which it rejects.
"""

import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/infra-lint.yml"
posix_only = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")


def _steps() -> dict[str, dict[str, Any]]:
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["lint"]["steps"]
    return {step.get("name"): step for step in steps}


def test_linters_are_pinned_and_findings_are_not_swallowed() -> None:
    steps = _steps()

    assert steps["Set up TFLint"]["with"]["tflint_version"] == "v0.64.0"
    assert "cfn-lint==" in steps["CloudFormation lint"]["run"]
    assert all("|| true" not in step.get("run", "") for step in steps.values())
    assert "!inputs.soft-fail" in steps["Fail on findings"]["if"]


def test_cfn_lint_only_runs_for_listed_templates() -> None:
    assert _steps()["CloudFormation lint"]["if"] == "inputs.cloudformation-templates != ''"


@posix_only
@pytest.mark.parametrize(("exit_code", "status"), [(0, "0"), (2, "1")])
def test_tflint_checks_each_path_recursively(tmp_path: Path, exit_code: int, status: str) -> None:
    fakebin = make_fakebin(tmp_path, {"tflint": f'echo "tflint $*"; exit {exit_code}'})

    result = run_workflow_step(
        WORKFLOW,
        "lint",
        "Terraform lint",
        context={"inputs.paths": "infra modules/net", "github.token": "token"},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    calls = [line for line in result.stdout.splitlines() if line.startswith("tflint")]
    assert calls == [
        "tflint --chdir infra --init",
        "tflint --chdir infra --recursive --format compact",
        "tflint --chdir modules/net --init",
        "tflint --chdir modules/net --recursive --format compact",
    ]
    assert result.outputs["status"] == status


@posix_only
def test_cfn_lint_reports_its_status(tmp_path: Path) -> None:
    fakebin = make_fakebin(
        tmp_path, {"python": "true", "cfn-lint": 'echo "cfn-lint $*"; exit 2'}
    )

    result = run_workflow_step(
        WORKFLOW,
        "lint",
        "CloudFormation lint",
        context={"inputs.cloudformation-templates": "stacks/*.yaml app.json"},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert "cfn-lint stacks/*.yaml app.json" in result.stdout
    assert result.outputs["status"] == "2"
