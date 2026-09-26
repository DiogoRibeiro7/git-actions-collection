"""An unsupported build-tool skipped both test steps and the job passed without testing."""

import os
from pathlib import Path

import pytest

from tests.utils.fake_runner import run_workflow_step

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/java-ci.yml"


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
@pytest.mark.parametrize(("tool", "code"), [("maven", 0), ("gradle", 0), ("sbt", 1), ("", 1)])
def test_only_supported_build_tools_are_accepted(tmp_path: Path, tool: str, code: int) -> None:
    result = run_workflow_step(
        WORKFLOW, "build", "Check build tool", context={"inputs.build-tool": tool}, workdir=tmp_path
    )

    assert result.code == code
    if code:
        assert "build-tool must be maven or gradle" in result.stdout
