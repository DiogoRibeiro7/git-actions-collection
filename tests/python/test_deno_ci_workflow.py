"""The deploy step ran inside the OS matrix, deploying to production once per OS."""

import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/deno-ci.yml"


def _jobs() -> dict[str, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]


def test_deployment_runs_once_after_every_os_passes() -> None:
    jobs = _jobs()

    assert all("deploy" not in step.get("name", "").lower() for step in jobs["build"]["steps"])
    assert jobs["deploy"]["needs"] == "build"
    assert jobs["deploy"]["if"] == "inputs.deploy == true"
    assert "strategy" not in jobs["deploy"]


def test_deploy_credentials_stay_out_of_the_script() -> None:
    deploy = next(step for step in _jobs()["deploy"]["steps"] if step.get("name") == "Deploy")

    assert "${{" not in deploy["run"]
    assert deploy["env"]["DENO_DEPLOY_TOKEN"] == "${{ secrets.deno-deploy-token }}"


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
@pytest.mark.parametrize(
    ("project", "token", "code", "message"),
    [
        ("", "t", 1, "project is required"),
        ("app", "", 1, "deno-deploy-token secret is required"),
        ("app", "t", 0, "deno run --allow-read --allow-net --allow-env"),
    ],
)
def test_deploy_requires_a_project_and_token(
    tmp_path: Path, project: str, token: str, code: int, message: str
) -> None:
    fakebin = make_fakebin(tmp_path, {"deno": 'echo "deno $*"'})

    result = run_workflow_step(
        WORKFLOW,
        "deploy",
        "Deploy",
        context={"secrets.deno-deploy-token": token, "inputs.project": project},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )

    assert result.code == code
    assert message in result.stdout + result.stderr
