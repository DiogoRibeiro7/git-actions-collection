import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.rust_steps import (
    cargo_stub,
    run_step,
)


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust benchmark smoke workflow."""
    path = Path(".github/workflows/rust-benchmark.yml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _workflow_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Return workflow_call inputs while handling YAML's reserved 'on' token."""
    on_block = data.get("on") or data.get(True)
    return on_block["workflow_call"]["inputs"]


def test_rust_benchmark_inputs_have_smoke_defaults() -> None:
    """Verify defaults favour fast execution rather than performance gating."""
    inputs = _workflow_inputs(_load_workflow())

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["locked"]["default"] is True
    assert inputs["bench-name"]["default"] == ""
    assert inputs["benchmark-filter"]["default"] == ""
    assert inputs["warm-up-seconds"]["default"] == 0.1
    assert inputs["measurement-seconds"]["default"] == 0.2
    assert inputs["sample-size"]["default"] == 10
    assert inputs["upload-results"]["default"] is False
    assert inputs["artifact-retention-days"]["default"] == 7
    assert inputs["use-cache"]["default"] is True


def test_rust_benchmark_uses_read_only_permissions() -> None:
    """Benchmark smoke tests should only need repository read access."""
    data = _load_workflow()

    assert data["permissions"] == {"contents": "read"}


def test_rust_benchmark_validates_criterion_ranges() -> None:
    """Criterion smoke inputs should fail clearly when invalid."""
    data = _load_workflow()
    steps = data["jobs"]["benchmark"]["steps"]
    validate = next(
        step for step in steps if step.get("name") == "Validate benchmark configuration"
    )

    assert "warm-up-seconds must be greater than 0" in validate["run"]
    assert "measurement-seconds must be greater than 0" in validate["run"]
    assert "sample-size must be at least 10 for Criterion" in validate["run"]
    assert "artifact-retention-days must be between 1 and 90" in validate["run"]


def test_rust_benchmark_builds_argument_arrays_safely() -> None:
    """Cargo and Criterion arguments should not be concatenated into shell strings."""
    data = _load_workflow()
    steps = data["jobs"]["benchmark"]["steps"]
    benchmark = next(
        step for step in steps if step.get("name") == "Run Criterion smoke benchmark"
    )

    assert "cargo_args=(--workspace)" in benchmark["run"]
    assert 'cargo_args+=(--bench "$BENCH_NAME")' in benchmark["run"]
    assert "criterion_args=(" in benchmark["run"]
    assert '--warm-up-time "$WARM_UP_SECONDS"' in benchmark["run"]
    assert '--measurement-time "$MEASUREMENT_SECONDS"' in benchmark["run"]
    assert '--sample-size "$SAMPLE_SIZE"' in benchmark["run"]
    assert 'cargo bench "${cargo_args[@]}" -- "${criterion_args[@]}"' in benchmark["run"]


def test_rust_benchmark_cache_is_best_effort() -> None:
    """Cache failures must not fail a valid benchmark smoke run."""
    data = _load_workflow()
    steps = data["jobs"]["benchmark"]["steps"]
    cache = next(step for step in steps if step.get("name") == "Restore Rust cache")

    assert cache["if"] == "inputs.use-cache"
    assert cache["continue-on-error"] is True
    assert cache["with"]["cache-on-failure"] is False


def test_rust_benchmark_result_upload_is_opt_in() -> None:
    """Criterion output should only be retained when explicitly requested."""
    data = _load_workflow()
    steps = data["jobs"]["benchmark"]["steps"]
    upload = next(
        step for step in steps if step.get("name") == "Upload Criterion results"
    )

    assert upload["if"] == "inputs.upload-results && success()"
    assert upload["with"]["path"] == "${{ inputs.working-directory }}/target/criterion"
    assert upload["with"]["if-no-files-found"] == "error"


def test_rust_benchmark_has_executable_self_test() -> None:
    """Exercise a real Criterion benchmark with deliberately short sampling."""
    path = Path(".github/workflows/test-rust-benchmark.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["rust-benchmark-example"]
    assert smoke["uses"] == "./.github/workflows/rust-benchmark.yml"
    assert smoke["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "locked": False,
        "bench-name": "add",
        "benchmark-filter": "add_two_numbers",
        "warm-up-seconds": 0.1,
        "measurement-seconds": 0.1,
        "sample-size": 10,
        "upload-results": False,
    }


posix_only = pytest.mark.skipif(os.name != "posix", reason="Fake runner requires bash (Linux CI)")

CONFLICTING_FEATURES = [
    ({"all-features": True, "no-default-features": True}, "cannot both be enabled"),
    ({"all-features": True, "features": "extra"}, "cannot be combined with an explicit feature list"),
]


@posix_only
@pytest.mark.parametrize(
    ("inputs", "message"),
    [
        *CONFLICTING_FEATURES,
        ({"warm-up-seconds": 0}, "warm-up-seconds must be greater than 0"),
        ({"measurement-seconds": 0}, "measurement-seconds must be greater than 0"),
        ({"sample-size": 9}, "sample-size must be at least 10 for Criterion"),
        ({"artifact-retention-days": 91}, "artifact-retention-days must be between 1 and 90"),
    ],
)
def test_rust_benchmark_rejects_invalid_configuration(
    tmp_path: Path, inputs: dict[str, Any], message: str
) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\n", encoding="utf-8")

    result = run_step(
        "rust-benchmark.yml",
        "benchmark",
        "Validate benchmark configuration",
        tmp_path,
        inputs=inputs,
    )

    assert result.code != 0
    assert message in result.stderr


@posix_only
@pytest.mark.parametrize(
    ("inputs", "expected"),
    [
        (
            {},
            "bench --workspace --locked -- "
            "--warm-up-time 0.1 --measurement-time 0.2 --sample-size 10",
        ),
        (
            {"bench-name": "add", "benchmark-filter": "add/small", "features": "extra"},
            "bench --workspace --locked --features extra --bench add -- add/small "
            "--warm-up-time 0.1 --measurement-time 0.2 --sample-size 10",
        ),
    ],
)
def test_rust_benchmark_passes_selection_and_timing_to_criterion(
    tmp_path: Path, inputs: dict[str, Any], expected: str
) -> None:
    """The filter must precede Criterion's own options after the `--` separator."""
    log = tmp_path / "cargo.log"
    result = run_step(
        "rust-benchmark.yml",
        "benchmark",
        "Run Criterion smoke benchmark",
        tmp_path,
        inputs=inputs,
        stubs=cargo_stub(log),
    )

    assert result.code == 0, result.stderr
    assert log.read_text(encoding="utf-8").splitlines() == [expected]


@posix_only
def test_rust_benchmark_propagates_benchmark_failures(tmp_path: Path) -> None:
    result = run_step(
        "rust-benchmark.yml",
        "benchmark",
        "Run Criterion smoke benchmark",
        tmp_path,
        stubs=cargo_stub(tmp_path / "cargo.log", exit_code=101),
    )

    assert result.code != 0
