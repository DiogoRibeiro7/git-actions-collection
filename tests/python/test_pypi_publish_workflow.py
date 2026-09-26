import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/pypi-publish.yml"


def _load() -> dict[Any, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_publish_reads_the_distributions_built_in_the_working_directory() -> None:
    """Actions ignore defaults.run.working-directory, so the publish step read ./dist."""
    publish = next(
        step for step in _load()["jobs"]["publish"]["steps"]
        if step.get("uses", "").startswith("pypa/gh-action-pypi-publish@")
    )

    assert publish["with"]["packages-dir"] == "${{ inputs.working-directory }}/dist"


def test_pre_release_is_described_as_the_testpypi_switch_it_is() -> None:
    data = _load()
    inputs = (data.get("on") or data.get(True))["workflow_call"]["inputs"]

    assert inputs["pre-release"]["description"].startswith("Upload to TestPyPI instead of PyPI")


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
@pytest.mark.parametrize(("backend", "command"), [("build", "python -m build"), ("poetry", "poetry build")])
def test_build_uses_the_requested_backend(tmp_path: Path, backend: str, command: str) -> None:
    fakebin = make_fakebin(
        tmp_path, {"python": 'echo "python $*"', "poetry": 'echo "poetry $*"'}
    )

    result = run_workflow_step(
        WORKFLOW,
        "publish",
        "Build",
        context={"inputs.build-backend": backend},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.stdout.splitlines() == [command]
