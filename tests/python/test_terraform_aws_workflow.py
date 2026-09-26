"""terraform destroy must only follow a failed apply.

The old condition, failure() && destroy-on-failure && apply, was also true when checkout,
AWS credentials, init or plan failed, so a typo destroyed every resource in the state.
"""

from pathlib import Path
from typing import Any

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/terraform-aws.yml"


def _steps() -> dict[str, dict[str, Any]]:
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["terraform"]["steps"]
    return {step.get("name"): step for step in steps}


def test_destroy_runs_only_after_the_apply_step_failed() -> None:
    steps = _steps()

    assert steps["Terraform Apply"]["id"] == "apply"
    assert steps["Destroy after a failed apply"]["if"] == (
        "failure() && steps.apply.outcome == 'failure' && inputs.destroy-on-failure == true"
    )


def test_no_other_step_destroys_infrastructure() -> None:
    destroying = [
        name for name, step in _steps().items() if "terraform destroy" in step.get("run", "")
    ]

    assert destroying == ["Destroy after a failed apply"]
