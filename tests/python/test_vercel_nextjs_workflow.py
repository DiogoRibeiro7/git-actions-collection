"""The deploy step captured `vercel deploy 2>&1`, so the CLI's banner and warnings went into
the URL, and the multi-line value made GITHUB_OUTPUT fail after a successful deploy."""

import os
from pathlib import Path

import pytest

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/vercel-nextjs.yml"
pytestmark = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
CONTEXT = {
    "inputs.working-directory": ".",
    "secrets.vercel-token": "token",
    "inputs.vercel-org-id": "team_1",
    "inputs.vercel-project-id": "prj_1",
    "inputs.prod": "true",
}


def _deploy(tmp_path: Path, npx: str):
    fakebin = make_fakebin(tmp_path / "tools", {"npx": npx, "sleep": "true"})
    return run_workflow_step(
        WORKFLOW,
        "deploy",
        "Deploy to Vercel",
        context=CONTEXT,
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )


def test_only_the_deployment_url_reaches_the_output(tmp_path: Path) -> None:
    npx = (
        'echo "Vercel CLI 33.7.1" >&2; echo "(node) DeprecationWarning" >&2; '
        'echo "args: $*" >&2; echo "https://app-abc.vercel.app"'
    )

    result = _deploy(tmp_path, npx)

    assert result.code == 0, result.stderr
    assert result.outputs["url"] == "https://app-abc.vercel.app"
    assert "--yes --prod" in result.stderr and "--confirm" not in result.stderr


def test_the_deploy_is_retried_and_its_failure_reported(tmp_path: Path) -> None:
    calls = tmp_path / "calls"
    result = _deploy(tmp_path, f'echo x >> "{calls}"; exit 3')

    assert result.code == 3
    assert calls.read_text(encoding="utf-8").count("x") == 3
    assert "Deploy failed (attempt 2); retrying" in result.stderr
