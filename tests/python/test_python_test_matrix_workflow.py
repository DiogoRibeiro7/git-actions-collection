import os
from pathlib import Path

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/python-test-matrix.yml"


def test_python_test_matrix_inputs_defaults():
    workflow_path = Path(".github/workflows/python-test-matrix.yml")
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    on_block = data.get("on") or data.get(True)
    inputs = on_block["workflow_call"]["inputs"]
    assert inputs["python-versions"]["default"] == '["3.10","3.11","3.12"]'
    assert inputs["os-matrix"]["default"] == '["ubuntu-latest","windows-latest","macos-latest"]'
    assert inputs["test-command"]["default"] == "pytest -q"
    assert inputs["pip-version"]["default"] == "24.3.1"


def test_python_test_matrix_strategy_uses_inputs():
    workflow_path = Path(".github/workflows/python-test-matrix.yml")
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    matrix = data["jobs"]["test"]["strategy"]["matrix"]
    assert "fromJson(inputs.python-versions)" in matrix["python"]
    assert "fromJson(inputs.os-matrix)" in matrix["os"]


def test_python_test_matrix_permissions_are_read_only():
    workflow_path = Path(".github/workflows/python-test-matrix.yml")
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    assert data["permissions"] == {"contents": "read"}


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
@pytest.mark.parametrize("exit_code", [0, 7])
def test_test_command_exit_status_is_propagated(tmp_path, exit_code):
    result = run_workflow_step(
        WORKFLOW,
        "test",
        "Run tests",
        context={"inputs.test-command": f"exit {exit_code}"},
        workdir=tmp_path,
    )
    assert result.code == exit_code


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
@pytest.mark.parametrize(
    "pip_version,expected",
    [
        ("24.3.1", "python -m pip install --upgrade pip==24.3.1"),
        ("latest", "python -m pip install --upgrade pip"),
    ],
)
@pytest.mark.parametrize(
    "manifest,install",
    [
        ("pyproject.toml", "pip install ."),
        ("requirements.txt", "pip install -r requirements.txt"),
        (None, None),
    ],
)
def test_install_step_selects_consumer_dependencies(
    tmp_path, pip_version, expected, manifest, install
):
    if manifest:
        (tmp_path / manifest).touch()
    fakebin = make_fakebin(tmp_path, {"python": 'echo "python $*"', "pip": 'echo "pip $*"'})
    result = run_workflow_step(
        WORKFLOW,
        "test",
        "Install project",
        context={"inputs.pip-version": pip_version},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )
    expected_commands = [expected, *([install] if install else []), "pip install pytest"]
    assert result.code == 0, result.stderr
    assert result.stdout.splitlines() == expected_commands


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
def test_failed_install_prevents_later_commands(tmp_path):
    fakebin = make_fakebin(tmp_path, {"python": "exit 9", "pip": "echo should-not-run"})
    result = run_workflow_step(
        WORKFLOW,
        "test",
        "Install project",
        context={"inputs.pip-version": "24.3.1"},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )
    assert result.code == 9
    assert result.stdout == ""
