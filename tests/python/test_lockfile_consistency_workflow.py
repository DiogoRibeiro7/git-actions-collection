import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/lockfile-consistency.yml"


def _load() -> dict[Any, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_poetry_is_pinned_and_python_is_set_up() -> None:
    data = _load()
    inputs = (data.get("on") or data.get(True))["workflow_call"]["inputs"]
    steps = [step.get("name") for step in data["jobs"]["check"]["steps"]]

    assert inputs["poetry-version"]["default"] == "2.5.1"
    assert steps.index("Set up Python") < steps.index("Check Poetry lock")


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
def test_poetry_check_uses_the_poetry_2_command(tmp_path: Path) -> None:
    """Poetry 2 removed `poetry lock --check`, which failed every run."""
    fakebin = make_fakebin(
        tmp_path, {"python": 'echo "python $*"', "poetry": 'echo "poetry $*"'}
    )

    result = run_workflow_step(
        WORKFLOW,
        "check",
        "Check Poetry lock",
        context={"inputs.pip-version": "26.2.1", "inputs.poetry-version": "2.5.1"},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.stdout.splitlines() == [
        "python -m pip install --upgrade pip==26.2.1",
        "python -m pip install poetry==2.5.1",
        "poetry check --lock",
    ]
