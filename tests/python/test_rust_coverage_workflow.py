from pathlib import Path
from typing import Any

import yaml


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust coverage workflow."""
    path = Path(".github/workflows/rust-coverage.yml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _workflow_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Return workflow_call inputs while handling YAML's reserved 'on' token."""
    on_block = data.get("on") or data.get(True)
    return on_block["workflow_call"]["inputs"]


def test_rust_coverage_inputs_have_safe_defaults() -> None:
    """Verify coverage is useful without imposing a global threshold."""
    inputs = _workflow_inputs(_load_workflow())

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["locked"]["default"] is True
    assert inputs["features"]["default"] == ""
    assert inputs["all-features"]["default"] is False
    assert inputs["no-default-features"]["default"] is False
    assert inputs["minimum-line-coverage"]["default"] == 0
    assert inputs["upload-lcov"]["default"] is True
    assert inputs["artifact-retention-days"]["default"] == 7
    assert inputs["use-cache"]["default"] is True


def test_rust_coverage_uses_read_only_permissions() -> None:
    """Coverage generation should require only repository read access."""
    data = _load_workflow()

    assert data["permissions"] == {"contents": "read"}


def test_rust_coverage_pins_tooling() -> None:
    """Coverage tooling and artifact handling should use immutable action SHAs."""
    data = _load_workflow()
    steps = data["jobs"]["coverage"]["steps"]
    steps_by_name = {step.get("name"): step for step in steps if step.get("name")}

    assert (
        steps_by_name["Install cargo-llvm-cov"]["uses"]
        == "taiki-e/install-action@7623a79cdfecb99d681017af368ca353d9f49bb5"
    )
    assert (
        steps_by_name["Install cargo-llvm-cov"]["with"]["tool"]
        == "cargo-llvm-cov@0.9.1"
    )
    assert (
        steps_by_name["Upload LCOV report"]["uses"]
        == "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f"
    )


def test_rust_coverage_builds_feature_and_threshold_arguments_safely() -> None:
    """Optional Cargo features and thresholds should use a Bash argument array."""
    data = _load_workflow()
    steps = data["jobs"]["coverage"]["steps"]
    generate = next(
        step for step in steps if step.get("name") == "Generate LCOV coverage"
    )

    assert 'args=(--workspace)' in generate["run"]
    assert 'args+=(--all-features)' in generate["run"]
    assert 'args+=(--no-default-features)' in generate["run"]
    assert 'args+=(--features "$CARGO_FEATURES")' in generate["run"]
    assert 'args+=(--fail-under-lines "$MINIMUM_LINE_COVERAGE")' in generate["run"]
    assert 'cargo llvm-cov "${args[@]}" --lcov --output-path lcov.info' in generate["run"]


def test_rust_coverage_validates_numeric_inputs() -> None:
    """Threshold and retention ranges should fail clearly before running tests."""
    data = _load_workflow()
    steps = data["jobs"]["coverage"]["steps"]
    validate = next(
        step for step in steps if step.get("name") == "Validate coverage configuration"
    )

    assert "minimum-line-coverage must be between 0 and 100" in validate["run"]
    assert "artifact-retention-days must be between 1 and 90" in validate["run"]


def test_rust_coverage_uploads_lcov_even_after_threshold_failure() -> None:
    """Coverage artifacts should remain available to diagnose a failed threshold."""
    data = _load_workflow()
    steps = data["jobs"]["coverage"]["steps"]
    upload = next(step for step in steps if step.get("name") == "Upload LCOV report")

    assert upload["if"] == "inputs.upload-lcov && always()"
    assert upload["with"]["path"] == "${{ inputs.working-directory }}/lcov.info"
    assert upload["with"]["if-no-files-found"] == "ignore"
    assert upload["with"]["retention-days"] == "${{ inputs.artifact-retention-days }}"


def test_rust_coverage_has_executable_self_test() -> None:
    """Exercise coverage generation and a non-zero threshold on the example crate."""
    path = Path(".github/workflows/test-rust-coverage.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["rust-coverage-example"]
    assert smoke["uses"] == "./.github/workflows/rust-coverage.yml"
    assert smoke["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "locked": False,
        "features": "extra",
        "minimum-line-coverage": 50,
        "artifact-retention-days": 1,
    }
