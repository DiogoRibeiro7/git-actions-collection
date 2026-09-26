import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.action_refs import action_name, is_commit_pinned
from tests.utils.rust_steps import (
    CLEAN_LIB,
    TEST_ONLY_CLIPPY_WARNING,
    UNFORMATTED_LIB,
    assert_gate,
    require_rust_tools,
    run_step,
    write_crate,
)


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust quality workflow."""
    workflow_path = Path(".github/workflows/rust-quality.yml")
    return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))


def _workflow_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Return workflow_call inputs while handling YAML's reserved 'on' token."""
    on_block = data.get("on") or data.get(True)
    return on_block["workflow_call"]["inputs"]


def test_rust_quality_inputs_have_safe_defaults() -> None:
    """Verify the public quality inputs have deterministic defaults."""
    inputs = _workflow_inputs(_load_workflow())

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["locked"]["default"] is True
    assert inputs["features"]["default"] == ""
    assert inputs["all-features"]["default"] is False
    assert inputs["no-default-features"]["default"] is False
    assert inputs["run-format"]["default"] is True
    assert inputs["run-clippy"]["default"] is True
    assert inputs["use-cache"]["default"] is True
    assert inputs["cache-targets"]["default"] is True


def test_rust_quality_uses_least_privilege() -> None:
    """Quality checks should require only read access to repository contents."""
    data = _load_workflow()

    assert data["permissions"] == {"contents": "read"}


def test_rust_quality_pins_external_actions() -> None:
    """Public workflow dependencies should use immutable commit SHAs."""
    data = _load_workflow()
    steps = data["jobs"]["quality"]["steps"]
    uses = {step["uses"]: action_name(step["uses"]) for step in steps if "uses" in step}

    assert set(uses.values()) >= {
        "actions/checkout",
        "dtolnay/rust-toolchain",
        "Swatinem/rust-cache",
    }
    assert all(is_commit_pinned(ref, action) for ref, action in uses.items())


def test_rust_quality_runs_fmt_and_clippy() -> None:
    """The workflow should expose independent format and Clippy quality gates."""
    data = _load_workflow()
    steps = data["jobs"]["quality"]["steps"]
    steps_by_name = {step.get("name"): step for step in steps if step.get("name")}

    assert steps_by_name["Format check"]["if"] == "inputs.run-format"
    assert "cargo fmt --all --check |" in steps_by_name["Format check"]["run"]

    clippy = steps_by_name["Clippy"]
    assert clippy["if"] == "inputs.run-clippy"
    assert "args=(--workspace --all-targets)" in clippy["run"]
    assert 'args+=(--all-features)' in clippy["run"]
    assert 'args+=(--no-default-features)' in clippy["run"]
    assert 'args+=(--features "$CARGO_FEATURES")' in clippy["run"]
    assert 'cargo clippy "${args[@]}" --message-format=json -- -D warnings' in clippy["run"]


def test_rust_quality_cache_is_best_effort() -> None:
    """Cache failures should not change the quality result."""
    data = _load_workflow()
    steps = data["jobs"]["quality"]["steps"]
    cache = next(step for step in steps if step.get("name") == "Restore Rust cache")

    assert cache["if"] == "inputs.use-cache"
    assert cache["continue-on-error"] is True
    assert cache["with"]["cache-on-failure"] is False


def test_rust_quality_has_executable_self_test() -> None:
    """Exercise the workflow against the repository's Rust example crate."""
    workflow_path = Path(".github/workflows/test-rust-quality.yml")
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["rust-quality-example"]
    assert smoke["uses"] == "./.github/workflows/rust-quality.yml"
    assert smoke["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "locked": False,
        "features": "extra",
    }


posix_only = pytest.mark.skipif(os.name != "posix", reason="Fake runner requires bash (Linux CI)")

CONFLICTING_FEATURES = [
    ({"all-features": True, "no-default-features": True}, "cannot both be enabled"),
    ({"all-features": True, "features": "extra"}, "cannot be combined with an explicit feature list"),
]


@posix_only
@pytest.mark.parametrize(
    ("step", "source", "failure"),
    [
        ("Format check", CLEAN_LIB, None),
        ("Format check", UNFORMATTED_LIB, "Diff in"),
        ("Clippy", CLEAN_LIB, None),
        # Unlike rust-ci, the quality gate lints tests and other targets too.
        ("Clippy", TEST_ONLY_CLIPPY_WARNING, "unneeded `return` statement"),
    ],
)
def test_rust_quality_gates_fail_on_broken_crates(
    tmp_path: Path, step: str, source: str, failure: str | None
) -> None:
    require_rust_tools("fmt", "clippy")
    crate = write_crate(tmp_path / "crate", source)

    result = run_step("rust-quality.yml", "quality", step, crate)

    assert_gate(result, failure)


@posix_only
@pytest.mark.parametrize(("inputs", "message"), CONFLICTING_FEATURES)
def test_rust_quality_rejects_conflicting_feature_flags(
    tmp_path: Path, inputs: dict[str, Any], message: str
) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\n", encoding="utf-8")

    result = run_step(
        "rust-quality.yml", "quality", "Validate Rust project", tmp_path, inputs=inputs
    )

    assert result.code != 0
    assert message in result.stderr
