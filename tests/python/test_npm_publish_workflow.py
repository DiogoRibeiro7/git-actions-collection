"""npm refuses to publish a version twice, so canaries published the package.json version
once and then failed on every later run."""

import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/npm-publish.yml"


def _load(path: Path) -> dict[Any, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_canaries_publish_a_unique_prerelease() -> None:
    npm = _load(ROOT / ".github/workflows/canary-release.yml")["jobs"]["npm"]

    assert npm["with"]["prerelease-id"] == "canary"
    assert npm["with"]["tag"] == "next"


def test_the_prerelease_version_is_set_before_publishing() -> None:
    names = [step.get("name") for step in _load(WORKFLOW)["jobs"]["publish"]["steps"]]

    assert names.index("Set prerelease version") == names.index("Publish") - 1


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
def test_the_prerelease_version_is_unique_per_run_attempt(tmp_path: Path) -> None:
    fakebin = make_fakebin(tmp_path, {"node": "echo 1.4.0", "npm": 'echo "npm $*"'})

    result = run_workflow_step(
        WORKFLOW,
        "publish",
        "Set prerelease version",
        context={"inputs.prerelease-id": "canary"},
        env={
            "PATH": f"{fakebin}:{os.environ['PATH']}",
            "GITHUB_RUN_NUMBER": "45",
            "GITHUB_RUN_ATTEMPT": "2",
        },
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.stdout.splitlines() == [
        "npm version --no-git-tag-version 1.4.0-canary.45.2",
        "Publishing 1.4.0-canary.45.2",
    ]
