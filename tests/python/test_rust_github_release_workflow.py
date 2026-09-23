from pathlib import Path
from typing import Any

import yaml


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust GitHub Release workflow."""
    path = Path(".github/workflows/rust-github-release.yml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _workflow_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Return workflow_call inputs while handling YAML's reserved 'on' token."""
    on_block = data.get("on") or data.get(True)
    return on_block["workflow_call"]["inputs"]


def test_rust_github_release_defaults_are_non_mutating() -> None:
    """Release creation must require an explicit live opt-in."""
    inputs = _workflow_inputs(_load_workflow())

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["package-name"]["default"] == ""
    assert inputs["locked"]["default"] is False
    assert inputs["tag-prefix"]["default"] == "v"
    assert inputs["tag-name"]["default"] == ""
    assert inputs["release-title"]["default"] == ""
    assert inputs["prerelease"]["default"] is False
    assert inputs["draft"]["default"] is False
    assert inputs["generate-notes"]["default"] is True
    assert inputs["dry-run"]["default"] is True
    assert inputs["release-environment"]["default"] == "release"
    assert inputs["artifact-retention-days"]["default"] == 7


def test_rust_github_release_reuses_verified_preflight() -> None:
    """GitHub Release assets should come from the existing release preflight."""
    data = _load_workflow()
    preflight = data["jobs"]["preflight"]

    assert preflight["uses"] == "./.github/workflows/rust-release-preflight.yml"
    assert preflight["with"]["upload-crate"] is True
    assert preflight["with"]["package-name"] == "${{ inputs.package-name }}"


def test_rust_github_release_generates_and_verifies_sha256() -> None:
    """Prepared release assets should include a checked SHA256SUMS file."""
    data = _load_workflow()
    steps = data["jobs"]["assets"]["steps"]
    steps_by_name = {step.get("name"): step for step in steps if step.get("name")}

    generate = steps_by_name["Generate SHA-256 checksums"]["run"]
    verify = steps_by_name["Verify checksum file"]["run"]

    assert "sha256sum ./*.crate > SHA256SUMS" in generate
    assert "sha256sum --check SHA256SUMS" in verify


def test_rust_github_release_uses_pinned_artifact_actions() -> None:
    """Artifact movement must use immutable action SHAs."""
    data = _load_workflow()
    rendered = Path(".github/workflows/rust-github-release.yml").read_text(
        encoding="utf-8"
    )

    assert (
        "actions/download-artifact@484a0b528fb4d7bd804637ccb632e47a0e638317"
        in rendered
    )
    assert (
        "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f"
        in rendered
    )


def test_rust_github_release_requires_version_tag_match() -> None:
    """Release tags should identify the Cargo package version exactly."""
    data = _load_workflow()
    steps = data["jobs"]["assets"]["steps"]
    resolve = next(step for step in steps if step.get("name") == "Resolve release identity")

    assert 'expected_tag="${TAG_PREFIX}${PACKAGE_VERSION}"' in resolve["run"]
    assert "tag-name must match Cargo package version" in resolve["run"]


def test_rust_github_release_live_job_is_protected() -> None:
    """The mutating job should be opt-in, environment-protected, and write-scoped."""
    data = _load_workflow()
    job = data["jobs"]["release"]

    assert job["if"] == "${{ !inputs.dry-run }}"
    assert job["environment"] == "${{ inputs.release-environment }}"
    assert job["permissions"] == {"contents": "write"}


def test_rust_github_release_blocks_unsafe_events() -> None:
    """Live release creation should only accept manual dispatch or matching tag pushes."""
    data = _load_workflow()
    steps = data["jobs"]["release"]["steps"]
    validate = next(
        step for step in steps if step.get("name") == "Validate live release context"
    )

    assert "workflow_dispatch" in validate["run"]
    assert '"refs/tags/$TAG_NAME"' in validate["run"]
    assert "Live GitHub Release creation is blocked for event" in validate["run"]


def test_rust_github_release_uses_generated_notes_and_verified_tag() -> None:
    """GitHub CLI should require an existing tag and optionally generate notes."""
    data = _load_workflow()
    steps = data["jobs"]["release"]["steps"]
    create = next(step for step in steps if step.get("name") == "Create GitHub Release")

    assert "--verify-tag" in create["run"]
    assert "args+=(--generate-notes)" in create["run"]
    assert "release-assets/*" in create["run"]


def test_rust_github_release_has_executable_dry_run_self_test() -> None:
    """Exercise packaging and checksums without creating a GitHub Release."""
    path = Path(".github/workflows/test-rust-github-release.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["rust-github-release-dry-run"]
    assert smoke["uses"] == "./.github/workflows/rust-github-release.yml"
    # The skipped release job's grant must be allowed or the run fails at startup.
    assert smoke["permissions"] == {"contents": "write"}
    assert smoke["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "package-name": "rust-crate",
        "tag-name": "v0.1.0",
        "dry-run": True,
        "artifact-retention-days": 1,
    }
