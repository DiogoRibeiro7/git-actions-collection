"""Contracts for the cross-repository merge dependency workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


def _load(name: str) -> dict[str, Any]:
    """Load one workflow while preserving YAML's parsed trigger key."""
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def _workflow_call(workflow: dict[str, Any]) -> dict[str, Any]:
    """Return the reusable-workflow interface."""
    triggers = workflow.get("on") or workflow.get(True) or {}
    return triggers["workflow_call"]


def test_merge_gate_exposes_a_fail_closed_interface() -> None:
    workflow = _load("cross-repo-merge-gate.yml")
    call = _workflow_call(workflow)

    assert workflow["permissions"] == {"statuses": "write"}
    assert call["inputs"]["dependencies"]["required"] is True
    assert call["inputs"]["head-sha"]["default"] == ""
    assert call["inputs"]["status-context"]["default"] == "cross-repo-merge-gate"
    assert call["secrets"]["dependency-token"]["required"] is False

    steps = workflow["jobs"]["gate"]["steps"]
    assert any(step.get("id") == "evaluate" for step in steps)
    assert any(step.get("name") == "Publish required commit status" for step in steps)
    enforce = next(step for step in steps if step.get("name") == "Enforce merge gate")
    assert "steps.evaluate.outputs.state != 'success'" in enforce["if"]


def test_merge_gate_targets_the_pull_request_head_by_default() -> None:
    workflow = _load("cross-repo-merge-gate.yml")
    publish = next(
        step
        for step in workflow["jobs"]["gate"]["steps"]
        if step.get("name") == "Publish required commit status"
    )

    assert (
        publish["env"]["HEAD_SHA"]
        == "${{ inputs['head-sha'] || github.event.pull_request.head.sha || github.sha }}"
    )
    assert "repos/${GITHUB_REPOSITORY}/statuses/${HEAD_SHA}" in publish["run"]


def test_notifier_only_runs_for_merged_pull_requests() -> None:
    workflow = _load("notify-cross-repo-dependents.yml")
    call = _workflow_call(workflow)

    assert workflow["permissions"] == {}
    assert call["inputs"]["targets"]["required"] is True
    assert call["secrets"]["dispatch-token"]["required"] is True

    notify = workflow["jobs"]["notify"]
    assert (
        notify["if"]
        == "github.event_name == 'pull_request' && github.event.pull_request.merged == true"
    )
    run = notify["steps"][0]["run"]
    assert "/actions/workflows/${workflow}/dispatches" in run
    assert '{ref: $ref, inputs: {"head-sha": $head_sha}}' in run
