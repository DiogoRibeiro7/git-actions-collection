from pathlib import Path
from typing import Any

import yaml


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust publish workflow."""
    path = Path(".github/workflows/rust-publish.yml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _workflow_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Return workflow_call inputs while handling YAML's reserved 'on' token."""
    on_block = data.get("on") or data.get(True)
    return on_block["workflow_call"]["inputs"]


def test_rust_publish_defaults_to_dry_run() -> None:
    """Publishing must require an explicit opt-in to mutate crates.io."""
    inputs = _workflow_inputs(_load_workflow())

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["package-name"]["default"] == ""
    assert inputs["locked"]["default"] is False
    assert inputs["dry-run"]["default"] is True
    assert inputs["release-environment"]["default"] == "release"


def test_rust_publish_dry_run_has_no_oidc_permission() -> None:
    """Dry runs should not request an identity token."""
    data = _load_workflow()
    job = data["jobs"]["dry-run"]

    assert job["if"] == "inputs.dry-run"
    assert job["permissions"] == {"contents": "read"}
    assert "environment" not in job


def test_rust_publish_live_job_requires_oidc_and_environment() -> None:
    """Live publishing must run through an environment with OIDC enabled."""
    data = _load_workflow()
    job = data["jobs"]["publish"]

    assert job["if"] == "${{ !inputs.dry-run }}"
    assert job["environment"] == "${{ inputs.release-environment }}"
    assert job["permissions"] == {
        "contents": "read",
        "id-token": "write",
    }


def test_rust_publish_uses_pinned_trusted_publishing_action() -> None:
    """crates.io authentication should use the official pinned OIDC action."""
    data = _load_workflow()
    steps = data["jobs"]["publish"]["steps"]
    auth = next(step for step in steps if step.get("name") == "Authenticate to crates.io")

    assert auth["id"] == "crates-io-auth"
    assert (
        auth["uses"]
        == "rust-lang/crates-io-auth-action@4920f0933d6c80323414a03df1731d6678d52a1b"
    )


def test_rust_publish_does_not_support_long_lived_token_secrets() -> None:
    """The workflow should only consume the short-lived OIDC token output."""
    data = _load_workflow()
    rendered = Path(".github/workflows/rust-publish.yml").read_text(encoding="utf-8")

    assert "secrets." not in rendered
    assert "CRATES_IO_TOKEN" not in rendered
    assert "CARGO_REGISTRY_TOKEN" in rendered
    assert "${{ steps.crates-io-auth.outputs.token }}" in rendered


def test_rust_publish_blocks_unsafe_live_events() -> None:
    """Only releases, manual dispatches, and tag pushes may publish."""
    data = _load_workflow()
    steps = data["jobs"]["publish"]["steps"]
    validate = next(
        step for step in steps if step.get("name") == "Validate live publication context"
    )

    assert "release|workflow_dispatch" in validate["run"]
    assert 'refs/tags/*' in validate["run"]
    assert "Live crates.io publication is blocked for event" in validate["run"]


def test_rust_publish_never_disables_cargo_verification() -> None:
    """Neither dry-run nor live publication may bypass Cargo package verification."""
    data = _load_workflow()

    for job_name in ("dry-run", "publish"):
        steps = data["jobs"][job_name]["steps"]
        publish_steps = [
            step
            for step in steps
            if isinstance(step.get("run"), str) and "cargo publish" in step["run"]
        ]
        assert publish_steps
        for step in publish_steps:
            assert "--no-verify" not in step["run"]
            assert "--allow-dirty" not in step["run"]


def test_rust_publish_has_executable_dry_run_self_test() -> None:
    """Exercise packaging without requesting OIDC or uploading to crates.io."""
    path = Path(".github/workflows/test-rust-publish.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["rust-publish-dry-run"]
    assert smoke["uses"] == "./.github/workflows/rust-publish.yml"
    assert smoke["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "package-name": "rust-crate",
        "locked": False,
        "dry-run": True,
    }
