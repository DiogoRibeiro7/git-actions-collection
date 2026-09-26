import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.action_refs import is_commit_pinned
from tests.utils.rust_steps import (
    cargo_stub,
    run_step,
)


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

    assert is_commit_pinned(
        steps_by_name["Install cargo-llvm-cov"]["uses"], "taiki-e/install-action"
    )
    assert (
        steps_by_name["Install cargo-llvm-cov"]["with"]["tool"]
        == "cargo-llvm-cov@0.9.1"
    )
    assert is_commit_pinned(
        steps_by_name["Upload LCOV report"]["uses"], "actions/upload-artifact"
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


posix_only = pytest.mark.skipif(os.name != "posix", reason="Fake runner requires bash (Linux CI)")

CONFLICTING_FEATURES = [
    ({"all-features": True, "no-default-features": True}, "cannot both be enabled"),
    ({"all-features": True, "features": "extra"}, "cannot be combined with an explicit feature list"),
]


@posix_only
@pytest.mark.parametrize(
    ("minimum", "expected"),
    [
        (0, "llvm-cov --workspace --locked --lcov --output-path lcov.info"),
        (
            80,
            "llvm-cov --workspace --locked --fail-under-lines 80 --lcov --output-path lcov.info",
        ),
    ],
)
def test_rust_coverage_enforces_threshold_only_when_set(
    tmp_path: Path, minimum: int, expected: str
) -> None:
    log = tmp_path / "cargo.log"
    result = run_step(
        "rust-coverage.yml",
        "coverage",
        "Generate LCOV coverage",
        tmp_path,
        inputs={"minimum-line-coverage": minimum},
        stubs=cargo_stub(log),
    )

    assert result.code == 0, result.stderr
    assert log.read_text(encoding="utf-8").splitlines() == [expected]


@posix_only
def test_rust_coverage_fails_when_the_threshold_is_missed(tmp_path: Path) -> None:
    """cargo-llvm-cov exits non-zero below --fail-under-lines; the step must propagate it."""
    result = run_step(
        "rust-coverage.yml",
        "coverage",
        "Generate LCOV coverage",
        tmp_path,
        inputs={"minimum-line-coverage": 80},
        stubs=cargo_stub(tmp_path / "cargo.log", exit_code=1),
    )

    assert result.code != 0


@posix_only
@pytest.mark.parametrize(
    ("inputs", "message"),
    [
        *CONFLICTING_FEATURES,
        ({"minimum-line-coverage": 101}, "minimum-line-coverage must be between 0 and 100"),
        ({"minimum-line-coverage": -1}, "minimum-line-coverage must be between 0 and 100"),
        ({"artifact-retention-days": 91}, "artifact-retention-days must be between 1 and 90"),
    ],
)
def test_rust_coverage_rejects_invalid_configuration(
    tmp_path: Path, inputs: dict[str, Any], message: str
) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\n", encoding="utf-8")

    result = run_step(
        "rust-coverage.yml", "coverage", "Validate coverage configuration", tmp_path, inputs=inputs
    )

    assert result.code != 0
    assert message in result.stderr


@posix_only
@pytest.mark.parametrize("has_report", [True, False])
def test_rust_coverage_summary_tolerates_a_missing_report(
    tmp_path: Path, has_report: bool
) -> None:
    """The always() summary must not mask the real failure with a second one."""
    if has_report:
        (tmp_path / "lcov.info").write_text("TN:\n", encoding="utf-8")
    log = tmp_path / "cargo.log"

    result = run_step(
        "rust-coverage.yml",
        "coverage",
        "Coverage summary",
        tmp_path,
        stubs=cargo_stub(log),
        context={"steps.coverage.outcome": "success" if has_report else "failure"},
    )

    assert result.code == 0, result.stderr
    if has_report:
        assert log.read_text(encoding="utf-8").splitlines() == ["llvm-cov report --summary-only"]
    else:
        assert not log.exists()
        assert "Coverage report was not generated." in result.stderr
