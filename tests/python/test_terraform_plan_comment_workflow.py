import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/terraform-plan-comment.yml"
posix_only = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")


def _steps() -> list[dict[str, Any]]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["plan"]["steps"]


def test_a_failed_plan_is_posted_and_then_fails_the_job() -> None:
    names = [step.get("name") for step in _steps()]
    by_name = {step.get("name"): step for step in _steps()}

    assert names.index("Plan") < names.index("Comment PR with plan") < names.index(
        "Fail when the plan failed"
    )
    assert by_name["Plan"]["shell"] == "bash"
    assert by_name["Fail when the plan failed"]["if"] == "steps.tfplan.outputs.exit-code != '0'"


@posix_only
@pytest.mark.parametrize("status", [0, 1])
def test_plan_step_records_the_exit_code_and_output(tmp_path: Path, status: int) -> None:
    fakebin = make_fakebin(
        tmp_path, {"terraform": f'echo "plan output"; echo "plan error" >&2; exit {status}'}
    )

    result = run_workflow_step(
        WORKFLOW,
        "plan",
        "Plan",
        context={"inputs.working-directory": "."},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.outputs["exit-code"] == str(status)
    assert (tmp_path / "plan.txt").read_text(encoding="utf-8") == "plan output\nplan error\n"
    assert "plan error" in result.stdout


@posix_only
def test_fail_step_reports_the_plan_status(tmp_path: Path) -> None:
    result = run_workflow_step(
        WORKFLOW,
        "plan",
        "Fail when the plan failed",
        context={"steps.tfplan.outputs.exit-code": "1"},
        workdir=tmp_path,
    )

    assert result.code == 1
    assert "::error::terraform plan exited with status 1" in result.stdout
