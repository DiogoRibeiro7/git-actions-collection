import os
from pathlib import Path
import sys

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
    assert inputs["pip-version"]["default"] == "26.2.1"


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
        ("26.2.1", "python -m pip install --upgrade pip==26.2.1"),
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
        context={"inputs.pip-version": "26.2.1"},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )
    assert result.code == 9
    assert result.stdout == ""


posix_only = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")

SAMPLE_TESTS = """\
import pytest


def test_passes():
    assert True


def helper():
    assert 1 == 2


def test_fails():
    helper()


@pytest.mark.skip(reason="not today")
def test_skipped():
    pass


def test_errors(missing_fixture):
    pass
"""
MATRIX = {"matrix.python": "3.12", "matrix.os": "ubuntu-latest"}


def _annotations(stdout: str) -> list[str]:
    return [line for line in stdout.splitlines() if line.startswith("::")]


@posix_only
def test_run_tests_asks_pytest_for_a_junit_report_with_forward_slashes(tmp_path):
    """On Windows RUNNER_TEMP has backslashes, which pytest's PYTEST_ADDOPTS parsing drops."""
    result = run_workflow_step(
        WORKFLOW,
        "test",
        "Run tests",
        context={"inputs.test-command": 'printf "%s" "$PYTEST_ADDOPTS"'},
        env={"RUNNER_TEMP": r"D:\a\_temp"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.stdout == "--junitxml='D:/a/_temp/pytest-junit.xml'"


@posix_only
def test_summary_counts_pytest_results_and_annotates_failures(tmp_path):
    project = tmp_path / "project"
    (project / "tests").mkdir(parents=True)
    (project / "tests" / "test_sample.py").write_text(SAMPLE_TESTS, encoding="utf-8")
    temp = tmp_path / "runner-temp"
    temp.mkdir()
    env = {"RUNNER_TEMP": str(temp), "GITHUB_WORKSPACE": str(project)}

    tests = run_workflow_step(
        WORKFLOW,
        "test",
        "Run tests",
        context={"inputs.test-command": f"{sys.executable} -m pytest -q -p no:cacheprovider tests"},
        env=env,
        workdir=project,
    )
    summary = run_workflow_step(
        WORKFLOW,
        "test",
        "Summary",
        context={"steps.tests.outcome": "failure", **MATRIX},
        env=env,
        workdir=project,
    )

    assert tests.code == 1, tests.stdout
    assert summary.code == 0, summary.stderr
    assert summary.summary.startswith(
        "## Python 3.12 on ubuntu-latest\n\n| Check | Result |\n| --- | --- |\n"
        "| Tests | ❌ Failed: 1 passed, 1 failed, 1 error, 1 skipped in "
    )
    assert "| `tests.test_sample.test_fails` | assert 1 == 2 |" in summary.summary
    missing = "| `tests.test_sample.test_errors` | fixture 'missing_fixture' not found |"
    assert missing in summary.summary
    # The failure is annotated at the assertion inside the helper, the deepest frame.
    helper_line = SAMPLE_TESTS.splitlines().index("    assert 1 == 2") + 1
    annotations = _annotations(summary.stdout)
    assert annotations[0] == (
        f"::error file=tests/test_sample.py,line={helper_line},title=pytest"
        "::tests.test_sample.test_fails failed: assert 1 == 2"
    )
    # A setup error's report ends with "path:line" and no exception name, so it has no place.
    assert annotations[1] == (
        "::error title=pytest::tests.test_sample.test_errors failed: "
        "fixture 'missing_fixture' not found"
    )
    assert len(annotations) == 2


@posix_only
@pytest.mark.parametrize("encoding", ["utf-8", "cp1252"])
def test_summary_without_a_junit_report(tmp_path, encoding):
    """A test command that is not pytest writes no report; the result is still shown.

    cp1252 is the Windows runners' default, which cannot encode the result emoji.
    """
    result = run_workflow_step(
        WORKFLOW,
        "test",
        "Summary",
        context={"steps.tests.outcome": "success", **MATRIX},
        env={"RUNNER_TEMP": str(tmp_path), "PYTHONIOENCODING": encoding},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert "Could not write the summary" not in result.stdout, result.stderr
    assert "| Tests | ✅ Passed |" in result.stdout
    assert result.summary == (
        "## Python 3.12 on ubuntu-latest\n\n| Check | Result |\n| --- | --- |\n"
        "| Tests | ✅ Passed |\n\n"
        "No pytest JUnit report was written, so there are no test counts.\n"
    )
    assert _annotations(result.stdout) == []
