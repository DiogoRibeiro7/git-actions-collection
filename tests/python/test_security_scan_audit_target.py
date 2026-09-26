"""pip-audit must audit the caller's dependencies, never its own environment.

Without a target, pip-audit audits the environment it runs in, which here was the
scanner venv. And with the venvs in the workspace, Bandit scanned the scanners'
own site-packages under the default `paths: .`.
"""

import json
import os
from pathlib import Path

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/security-scan.yml"
pytestmark = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")

# Creates venvs that use this same script, and freezes a fixed environment.
FAKE_PYTHON = r"""
case "$*" in
  "-m venv "*) mkdir -p "$3/bin"; cp "$0" "$3/bin/python" ;;
  "-m pip freeze"*) printf 'requests==2.32.3\npip==26.2.1\ndemo @ file:///work\n' ;;
  *) echo "python $*" >&2 ;;
esac
"""


def _prepare(tmp_path: Path, install_command: str = "") -> tuple[str, str]:
    fakebin = make_fakebin(tmp_path / "tools", {"python": FAKE_PYTHON})
    result = run_workflow_step(
        WORKFLOW,
        "security",
        "Prepare Python dependency audit target",
        context={
            "inputs.dependency-install-command": install_command,
            "inputs.pip-version": "26.2.1",
        },
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )
    assert result.code == 0, result.stderr
    return result.outputs["requirements"], result.stdout


def test_root_requirements_file_is_audited(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.32.3\n", encoding="utf-8")

    assert _prepare(tmp_path)[0] == "requirements.txt"


def test_pyproject_dependencies_are_resolved_and_audited(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    requirements, _ = _prepare(tmp_path)

    assert requirements == ".security-scan-audit-requirements.txt"
    # The project itself and packaging tools are not audited as dependencies.
    assert (tmp_path / requirements).read_text(encoding="utf-8") == "requests==2.32.3\n"


def test_installed_dependencies_are_audited_when_a_command_is_given(tmp_path: Path) -> None:
    requirements, _ = _prepare(tmp_path, install_command="true")

    assert requirements == ".security-scan-audit-requirements.txt"


def test_nothing_to_audit_is_reported_not_hidden(tmp_path: Path) -> None:
    requirements, stdout = _prepare(tmp_path)

    assert requirements == ""
    assert "::warning::pip-audit skipped" in stdout


@pytest.mark.parametrize("requirements", ["", "requirements.txt"])
def test_pip_audit_only_ever_runs_against_a_requirements_file(
    tmp_path: Path, requirements: str
) -> None:
    runner_temp = tmp_path / "runner-temp"
    tools = runner_temp / "security-scan-tools" / "bin"
    tools.mkdir(parents=True)
    for tool in ("pip-audit", "bandit"):
        (tools / tool).write_text(
            f'#!/usr/bin/env bash\necho "{tool} $*" >> "{tmp_path}/calls"\n', encoding="utf-8"
        )
        (tools / tool).chmod(0o755)
    (tmp_path / "requirements.txt").write_text("requests==2.32.3\n", encoding="utf-8")

    result = run_workflow_step(
        WORKFLOW,
        "security",
        "Python dependency scans",
        context={
            "inputs.paths": ".",
            "inputs.bandit-args": "-ll -ii",
            "steps.audit-target.outputs.requirements": requirements,
        },
        env={"RUNNER_TEMP": str(runner_temp)},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    calls = (tmp_path / "calls").read_text(encoding="utf-8").splitlines()
    audits = [call for call in calls if call.startswith("pip-audit")]
    if requirements:
        assert audits == [
            "pip-audit --strict --format json -o pip-audit.json --requirement requirements.txt"
        ]
    else:
        assert audits == []
        assert json.loads((tmp_path / "pip-audit.json").read_text()) == {
            "dependencies": [],
            "fixes": [],
        }
    assert result.outputs["pip-audit-status"] == "0"


def test_scanner_environments_live_outside_the_workspace() -> None:
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["security"]["steps"]
    scripts = "\n".join(step.get("run", "") for step in steps)

    assert "venv .security-scan" not in scripts
    assert 'python -m venv "$RUNNER_TEMP/security-scan-tools"' in scripts
    assert 'python -m venv "$RUNNER_TEMP/security-scan-project"' in scripts


@pytest.mark.parametrize("committed", [True, False])
def test_gradle_verifies_against_committed_checksums(tmp_path: Path, committed: bool) -> None:
    """--write-verification-metadata rewrote the checksums instead of checking them."""
    gradlew = tmp_path / "gradlew"
    gradlew.write_text('#!/usr/bin/env bash\necho "gradlew $*"\n', encoding="utf-8")
    gradlew.chmod(0o755)
    if committed:
        (tmp_path / "gradle").mkdir()
        (tmp_path / "gradle/verification-metadata.xml").write_text("<x/>", encoding="utf-8")

    result = run_workflow_step(
        WORKFLOW, "security", "Verify Gradle dependencies", context={}, workdir=tmp_path
    )

    assert result.code == 0, result.stderr
    if committed:
        assert result.stdout.splitlines() == [
            "gradlew --no-daemon --dependency-verification strict dependencies"
        ]
    else:
        assert "::warning::Gradle dependency verification skipped" in result.stdout
        assert not any(line.startswith("gradlew ") for line in result.stdout.splitlines())
