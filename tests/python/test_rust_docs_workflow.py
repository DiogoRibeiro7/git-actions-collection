from pathlib import Path
from typing import Any

import yaml


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust documentation workflow."""
    path = Path(".github/workflows/rust-docs.yml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _workflow_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Return workflow_call inputs while handling YAML's reserved 'on' token."""
    on_block = data.get("on") or data.get(True)
    return on_block["workflow_call"]["inputs"]


def test_rust_docs_inputs_have_safe_defaults() -> None:
    """Verify documentation defaults keep the check strict and inexpensive."""
    inputs = _workflow_inputs(_load_workflow())

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["locked"]["default"] is True
    assert inputs["features"]["default"] == ""
    assert inputs["all-features"]["default"] is False
    assert inputs["no-default-features"]["default"] is False
    assert inputs["include-dependencies"]["default"] is False
    assert inputs["document-private-items"]["default"] is False
    assert inputs["upload-docs"]["default"] is False
    assert inputs["artifact-retention-days"]["default"] == 7
    assert inputs["use-cache"]["default"] is True


def test_rust_docs_uses_read_only_permissions() -> None:
    """Documentation builds should only need repository read access."""
    data = _load_workflow()

    assert data["permissions"] == {"contents": "read"}


def test_rust_docs_treats_rustdoc_warnings_as_errors() -> None:
    """The docs gate must fail on rustdoc warnings."""
    data = _load_workflow()
    steps = data["jobs"]["docs"]["steps"]
    build = next(step for step in steps if step.get("name") == "Build documentation")

    assert build["env"]["RUSTDOCFLAGS"] == "-D warnings"
    assert 'cargo doc "${args[@]}"' in build["run"]


def test_rust_docs_builds_cargo_arguments_safely() -> None:
    """Optional documentation modes should use a Bash argument array."""
    data = _load_workflow()
    steps = data["jobs"]["docs"]["steps"]
    build = next(step for step in steps if step.get("name") == "Build documentation")

    assert "args=(--workspace)" in build["run"]
    assert 'args+=(--all-features)' in build["run"]
    assert 'args+=(--no-default-features)' in build["run"]
    assert 'args+=(--features "$CARGO_FEATURES")' in build["run"]
    assert 'args+=(--no-deps)' in build["run"]
    assert 'args+=(--document-private-items)' in build["run"]


def test_rust_docs_cache_is_best_effort() -> None:
    """A cache backend problem must not fail an otherwise valid docs build."""
    data = _load_workflow()
    steps = data["jobs"]["docs"]["steps"]
    cache = next(step for step in steps if step.get("name") == "Restore Rust cache")

    assert cache["if"] == "inputs.use-cache"
    assert cache["continue-on-error"] is True
    assert cache["with"]["cache-on-failure"] is False


def test_rust_docs_upload_is_opt_in() -> None:
    """Generated HTML should only be retained when a caller asks for it."""
    data = _load_workflow()
    steps = data["jobs"]["docs"]["steps"]
    upload = next(
        step for step in steps if step.get("name") == "Upload HTML documentation"
    )

    assert upload["if"] == "inputs.upload-docs && success()"
    assert upload["with"]["path"] == "${{ inputs.working-directory }}/target/doc"
    assert upload["with"]["if-no-files-found"] == "error"


def test_rust_docs_has_executable_self_test() -> None:
    """Exercise strict rustdoc generation against the maintained example crate."""
    path = Path(".github/workflows/test-rust-docs.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["rust-docs-example"]
    assert smoke["uses"] == "./.github/workflows/rust-docs.yml"
    assert smoke["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "locked": False,
        "features": "extra",
        "document-private-items": True,
        "upload-docs": False,
    }
