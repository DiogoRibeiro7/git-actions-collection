from pathlib import Path
from typing import Any

import yaml


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust CI workflow."""
    workflow_path = Path(".github/workflows/rust-ci.yml")
    return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))


def test_rust_ci_inputs_have_safe_defaults() -> None:
    """Verify the public Rust CI inputs and compatibility-oriented defaults."""
    data = _load_workflow()

    on_block = data.get("on") or data.get(True)
    inputs = on_block["workflow_call"]["inputs"]

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["locked"]["default"] is True
    assert inputs["run-format"]["default"] is True
    assert inputs["run-clippy"]["default"] is True
    assert inputs["run-tests"]["default"] is True


def test_rust_ci_uses_least_privilege() -> None:
    """The reusable workflow should only need read access to repository contents."""
    data = _load_workflow()

    assert data["permissions"] == {"contents": "read"}


def test_rust_ci_runs_check_clippy_and_tests() -> None:
    """Ensure the workflow performs the core Rust verification stages."""
    data = _load_workflow()
    steps = data["jobs"]["build"]["steps"]
    steps_by_name = {step.get("name"): step for step in steps if step.get("name")}

    assert steps_by_name["Cargo check"]["run"] == "cargo check --workspace $LOCKED_FLAG"
    assert steps_by_name["Clippy"]["run"] == (
        "cargo clippy --workspace $LOCKED_FLAG -- -D warnings"
    )
    assert steps_by_name["Tests"]["run"] == "cargo test --workspace $LOCKED_FLAG"
    assert steps_by_name["Tests"]["if"] == "inputs.run-tests"


def test_rust_ci_honours_working_directory() -> None:
    """Run every Cargo command from the caller-selected crate or workspace."""
    data = _load_workflow()
    steps = data["jobs"]["build"]["steps"]

    cargo_steps = [
        step
        for step in steps
        if isinstance(step.get("run"), str) and "cargo " in step["run"]
    ]

    assert cargo_steps
    assert all(
        step["working-directory"] == "${{ inputs.working-directory }}"
        for step in cargo_steps
    )


def test_rust_ci_has_executable_self_test() -> None:
    """Exercise the reusable workflow against the repository's Rust example crate."""
    workflow_path = Path(".github/workflows/test-rust-ci.yml")
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["rust-example"]
    assert smoke["uses"] == "./.github/workflows/rust-ci.yml"
    assert smoke["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "locked": False,
    }
