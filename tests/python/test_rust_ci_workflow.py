import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.rust_steps import (
    CLEAN_LIB,
    COMPILE_ERROR_LIB,
    FAILING_TEST_LIB,
    FEATURE_GATED_LIB,
    LIB_CLIPPY_WARNING,
    UNFORMATTED_LIB,
    assert_gate,
    require_rust_tools,
    run_step,
    write_crate,
)


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust CI workflow."""
    workflow_path = Path(".github/workflows/rust-ci.yml")
    return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))


def _workflow_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Return workflow_call inputs while handling YAML's reserved 'on' token."""
    on_block = data.get("on") or data.get(True)
    return on_block["workflow_call"]["inputs"]


def test_rust_ci_inputs_have_safe_defaults() -> None:
    """Verify defaults keep the primary Rust CI job small and deterministic."""
    inputs = _workflow_inputs(_load_workflow())

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["locked"]["default"] is True
    assert inputs["features"]["default"] == ""
    assert inputs["all-features"]["default"] is False
    assert inputs["no-default-features"]["default"] is False
    assert inputs["run-format"]["default"] is True
    assert inputs["run-clippy"]["default"] is True
    assert inputs["run-tests"]["default"] is True
    assert inputs["use-cache"]["default"] is True
    assert inputs["cache-targets"]["default"] is True
    assert inputs["run-compatibility"]["default"] is False
    assert inputs["compatibility-toolchains"]["default"] == '["stable"]'
    assert inputs["compatibility-os"]["default"] == '["ubuntu-latest"]'


def test_rust_ci_uses_least_privilege() -> None:
    """The reusable workflow should only need read access to repository contents."""
    data = _load_workflow()

    assert data["permissions"] == {"contents": "read"}


def test_rust_ci_builds_feature_arguments_safely() -> None:
    """Cargo commands should use an argument array for optional feature flags."""
    data = _load_workflow()
    steps = data["jobs"]["build"]["steps"]
    steps_by_name = {step.get("name"): step for step in steps if step.get("name")}

    for step_name in ("Cargo check", "Clippy", "Tests"):
        command = steps_by_name[step_name]["run"]
        assert 'args=(--workspace)' in command
        assert 'args+=(--all-features)' in command
        assert 'args+=(--no-default-features)' in command
        assert 'args+=(--features "$CARGO_FEATURES")' in command

    assert 'cargo check "${args[@]}"' in steps_by_name["Cargo check"]["run"]
    assert 'cargo clippy "${args[@]}" -- -D warnings' in steps_by_name["Clippy"]["run"]
    assert 'cargo test "${args[@]}"' in steps_by_name["Tests"]["run"]


def test_rust_ci_honours_working_directory() -> None:
    """Run every Cargo command from the caller-selected crate or workspace."""
    data = _load_workflow()

    cargo_steps = []
    for job in data["jobs"].values():
        for step in job.get("steps", []):
            if isinstance(step.get("run"), str) and "cargo " in step["run"]:
                cargo_steps.append(step)

    assert cargo_steps
    assert all(
        step["working-directory"] == "${{ inputs.working-directory }}"
        for step in cargo_steps
    )


def test_rust_ci_cache_is_best_effort_and_primary_only() -> None:
    """Cache failures must never make a correct Rust build fail."""
    data = _load_workflow()
    build_steps = data["jobs"]["build"]["steps"]
    cache_steps = [
        step
        for step in build_steps
        if step.get("uses")
        == "Swatinem/rust-cache@f0d9c3887740aee45f6153b24b3a6b815192ec16"
    ]

    assert len(cache_steps) == 1
    cache = cache_steps[0]
    assert cache["if"] == "inputs.use-cache"
    assert cache["continue-on-error"] is True
    assert cache["with"]["workspaces"] == "${{ inputs.working-directory }} -> target"
    assert cache["with"]["cache-targets"] == "${{ inputs.cache-targets }}"
    assert cache["with"]["cache-on-failure"] is False

    compatibility_steps = data["jobs"]["compatibility"]["steps"]
    assert all(
        step.get("uses")
        != "Swatinem/rust-cache@f0d9c3887740aee45f6153b24b3a6b815192ec16"
        for step in compatibility_steps
    )


def test_rust_ci_compatibility_matrix_is_opt_in() -> None:
    """Compatibility testing must not multiply Actions usage by default."""
    data = _load_workflow()
    job = data["jobs"]["compatibility"]
    matrix = job["strategy"]["matrix"]

    assert job["if"] == "inputs.run-compatibility"
    assert job["runs-on"] == "${{ matrix.os }}"
    assert matrix["os"] == "${{ fromJSON(inputs.compatibility-os) }}"
    assert matrix["rust"] == "${{ fromJSON(inputs.compatibility-toolchains) }}"
    assert job["strategy"]["fail-fast"] is False


def test_rust_ci_has_executable_self_test() -> None:
    """Exercise feature inputs and one compatibility matrix cell."""
    workflow_path = Path(".github/workflows/test-rust-ci.yml")
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["rust-example"]
    assert smoke["uses"] == "./.github/workflows/rust-ci.yml"
    assert smoke["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "locked": False,
        "features": "extra",
        "run-compatibility": True,
        "compatibility-toolchains": '["stable"]',
        "compatibility-os": '["ubuntu-latest"]',
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
        ("Cargo check", CLEAN_LIB, None),
        ("Cargo check", COMPILE_ERROR_LIB, "cannot find value `missing`"),
        ("Clippy", CLEAN_LIB, None),
        ("Clippy", LIB_CLIPPY_WARNING, "unneeded `return` statement"),
        ("Tests", CLEAN_LIB, None),
        ("Tests", FAILING_TEST_LIB, "test result: FAILED"),
    ],
)
def test_rust_ci_gates_fail_on_broken_crates(
    tmp_path: Path, step: str, source: str, failure: str | None
) -> None:
    """Each primary CI gate must fail on the defect it exists to catch."""
    require_rust_tools("fmt", "clippy")
    crate = write_crate(tmp_path / "crate", source)

    result = run_step("rust-ci.yml", "build", step, crate)

    assert_gate(result, failure)


@posix_only
@pytest.mark.parametrize(
    ("inputs", "features", "failure"),
    [
        ({}, {"extra": []}, "the extra feature is required"),
        ({"features": "extra"}, {"extra": []}, None),
        ({"all-features": True}, {"extra": []}, None),
        ({}, {"default": ["extra"], "extra": []}, None),
        ({"no-default-features": True}, {"default": ["extra"], "extra": []}, "the extra feature is required"),
    ],
)
def test_rust_ci_passes_feature_selection_to_cargo(
    tmp_path: Path,
    inputs: dict[str, Any],
    features: dict[str, list[str]],
    failure: str | None,
) -> None:
    """Feature inputs must reach Cargo; the fixture only compiles with `extra` enabled."""
    require_rust_tools()
    crate = write_crate(tmp_path / "crate", FEATURE_GATED_LIB, features=features)

    for job, step in (("build", "Cargo check"), ("compatibility", "Compatibility check")):
        assert_gate(run_step("rust-ci.yml", job, step, crate, inputs=inputs), failure)


@posix_only
@pytest.mark.parametrize("job", ["build", "compatibility"])
@pytest.mark.parametrize(("inputs", "message"), CONFLICTING_FEATURES)
def test_rust_ci_rejects_conflicting_feature_flags(
    tmp_path: Path, job: str, inputs: dict[str, Any], message: str
) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\n", encoding="utf-8")

    result = run_step("rust-ci.yml", job, "Validate Rust project", tmp_path, inputs=inputs)

    assert result.code != 0
    assert message in result.stderr


@posix_only
def test_rust_ci_requires_a_cargo_manifest(tmp_path: Path) -> None:
    result = run_step("rust-ci.yml", "build", "Validate Rust project", tmp_path)

    assert result.code != 0
    assert "Cargo.toml not found in ." in result.stderr
