"""Contracts for the reusable immutable snapshot release workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "snapshot-release.yml"


def _load() -> dict[str, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _workflow_call(workflow: dict[str, Any]) -> dict[str, Any]:
    triggers = workflow.get("on") or workflow.get(True) or {}
    return triggers["workflow_call"]


def test_snapshot_release_interface_defaults_to_dry_run() -> None:
    workflow = _load()
    call = _workflow_call(workflow)
    inputs = call["inputs"]

    assert workflow["permissions"] == {"contents": "read"}
    assert inputs["snapshot-tag"]["required"] is True
    assert inputs["commit-sha"]["required"] is True
    assert inputs["artifact-name"]["required"] is True
    assert inputs["dry-run"]["default"] is True
    assert inputs["release-environment"]["default"] == "release"
    assert inputs["notes-file"]["default"] == "snapshot-summary.md"
    assert inputs["required-files"]["default"] == (
        '["snapshot-manifest.json","snapshot-summary.md"]'
    )


def test_validation_checks_tag_commit_artifact_and_existing_tag() -> None:
    workflow = _load()
    steps = workflow["jobs"]["validate"]["steps"]
    names = [step.get("name") for step in steps]

    assert names == [
        "Validate release inputs",
        "Check out requested commit",
        "Verify checkout identity",
        "Refuse an existing tag",
        "Download prepared release material",
        "Verify release material",
        "Dry-run summary",
    ]

    validate = steps[0]["run"]
    assert "snapshot-YYYY.MM.DD or snapshot-YYYY.MM.DD.N" in validate
    assert "[0-9a-f]{40}" in validate
    assert "required-files must be a non-empty JSON string array" in validate

    refuse = steps[3]["run"]
    assert "git ls-remote --exit-code --tags origin" in refuse


def test_live_publish_is_environment_protected_and_write_scoped() -> None:
    workflow = _load()
    publish = workflow["jobs"]["publish"]

    assert publish["if"] == "${{ !inputs.dry-run }}"
    assert publish["environment"] == "${{ inputs.release-environment }}"
    assert publish["permissions"] == {"contents": "write"}

    names = [step.get("name") for step in publish["steps"]]
    assert "Recheck tag absence" in names
    assert "Create immutable annotated tag" in names
    assert "Create GitHub Release" in names


def test_live_release_verifies_tag_and_uses_prepared_assets() -> None:
    workflow = _load()
    release = next(
        step
        for step in workflow["jobs"]["publish"]["steps"]
        if step.get("name") == "Create GitHub Release"
    )
    run = release["run"]

    assert 'gh release view "${SNAPSHOT_TAG}"' in run
    assert "find release-material -type f" in run
    assert "--verify-tag" in run
    assert '--target "${SNAPSHOT_COMMIT}"' in run
    assert '--notes-file "release-material/${NOTES_FILE}"' in run
