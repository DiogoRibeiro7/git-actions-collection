"""Jobs that can run on Windows must choose the shell for their `run` steps.

Windows runners default to PowerShell, so a bash script without `shell: bash`
fails there. python-test-matrix.yml shipped that bug: its default OS matrix
includes windows-latest, and every caller's Windows jobs failed to install.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _inputs(workflow: dict[Any, Any]) -> dict[str, Any]:
    triggers = workflow.get("on") or workflow.get(True) or {}
    call = triggers.get("workflow_call") if isinstance(triggers, dict) else None
    return (call or {}).get("inputs") or {}


def _mentions_windows(value: Any, inputs: dict[str, Any]) -> bool:
    """Whether a runs-on or matrix value can resolve to a Windows runner."""
    text = json.dumps(value) if not isinstance(value, str) else value
    defaults = [
        str((inputs.get(name) or {}).get("default", ""))
        for name in re.findall(r"inputs\.([\w-]+)", text)
    ]
    return "windows" in " ".join([text, *defaults]).lower()


def may_run_on_windows(job: dict[str, Any], inputs: dict[str, Any]) -> bool:
    runs_on = job.get("runs-on", "")
    matrix = (job.get("strategy") or {}).get("matrix") or {}
    if _mentions_windows(runs_on, inputs):
        return True
    return any(
        _mentions_windows(matrix.get(key), inputs)
        for key in re.findall(r"matrix\.([\w-]+)", json.dumps(runs_on))
    )


def unshelled_steps(workflow: dict[Any, Any]) -> list[str]:
    """Name the `run` steps of Windows-capable jobs that leave the shell to the runner."""
    inputs = _inputs(workflow)
    workflow_shell = ((workflow.get("defaults") or {}).get("run") or {}).get("shell")
    found = []
    for job_id, job in (workflow.get("jobs") or {}).items():
        if not may_run_on_windows(job, inputs):
            continue
        shell = ((job.get("defaults") or {}).get("run") or {}).get("shell") or workflow_shell
        found += [
            f"{job_id}: {step.get('name') or step['run'].splitlines()[0]}"
            for step in job.get("steps", [])
            if "run" in step and not (step.get("shell") or shell)
        ]
    return found


def test_windows_capable_jobs_choose_their_shell() -> None:
    problems = [
        f"{path.name} {step}"
        for path in sorted((ROOT / ".github" / "workflows").glob("*.y*ml"))
        for step in unshelled_steps(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    ]

    assert not problems, "Set `shell:` (or `defaults.run.shell`) for:\n" + "\n".join(problems)


MATRIX_JOB = {
    "runs-on": "${{ matrix.os }}",
    "strategy": {"matrix": {"os": "${{ fromJson(inputs.os-matrix) }}"}},
    "steps": [{"name": "Install", "run": "set -euo pipefail"}],
}


@pytest.mark.parametrize(
    ("workflow", "expected"),
    [
        (
            {True: {"workflow_call": {"inputs": {"os-matrix": {"default": '["windows-latest"]'}}}},
             "jobs": {"test": MATRIX_JOB}},
            ["test: Install"],
        ),
        (
            {True: {"workflow_call": {"inputs": {"os-matrix": {"default": '["ubuntu-latest"]'}}}},
             "jobs": {"test": MATRIX_JOB}},
            [],
        ),
        (
            {"jobs": {"test": {**MATRIX_JOB, "strategy": {"matrix": {"os": ["windows-2025"]}},
                               "defaults": {"run": {"shell": "bash"}}}}},
            [],
        ),
        (
            {"defaults": {"run": {"shell": "bash"}},
             "jobs": {"test": {"runs-on": "windows-latest", "steps": [{"run": "ls"}]}}},
            [],
        ),
        (
            {"jobs": {"test": {"runs-on": "windows-latest", "steps": [{"run": "ls", "shell": "pwsh"}, {"run": "dir"}]}}},
            ["test: dir"],
        ),
    ],
)
def test_unshelled_step_rules(workflow: dict[Any, Any], expected: list[str]) -> None:
    assert unshelled_steps(workflow) == expected
