from pathlib import Path
from typing import Any

import yaml


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust security workflow."""
    path = Path(".github/workflows/rust-security.yml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _workflow_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Return workflow_call inputs while handling YAML's reserved 'on' token."""
    on_block = data.get("on") or data.get(True)
    return on_block["workflow_call"]["inputs"]


def test_rust_security_inputs_have_safe_defaults() -> None:
    """Verify safe defaults for RustSec dependency auditing."""
    inputs = _workflow_inputs(_load_workflow())

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["generate-lockfile"]["default"] is True
    assert inputs["ignored-advisories"]["default"] == ""
    assert inputs["run-cargo-audit"]["default"] is True
    assert inputs["run-cargo-deny"]["default"] is False
    assert inputs["cargo-deny-config"]["default"] == "deny.toml"
    assert inputs["cargo-deny-checks"]["default"] == "advisories,bans,licenses,sources"


def test_rust_security_uses_read_only_permissions() -> None:
    """Dependency auditing should not need check, issue, or repository writes."""
    data = _load_workflow()

    assert data["permissions"] == {"contents": "read"}


def test_rust_security_pins_tooling() -> None:
    """Security tooling and actions must be pinned explicitly."""
    data = _load_workflow()
    steps = data["jobs"]["audit"]["steps"]
    steps_by_name = {step.get("name"): step for step in steps if step.get("name")}

    assert (
        steps_by_name["Install cargo-audit"]["uses"]
        == "taiki-e/install-action@7623a79cdfecb99d681017af368ca353d9f49bb5"
    )
    assert steps_by_name["Install cargo-audit"]["with"]["tool"] == "cargo-audit@0.22.2"
    assert (
        steps_by_name["Install cargo-deny"]["uses"]
        == "taiki-e/install-action@7623a79cdfecb99d681017af368ca353d9f49bb5"
    )
    assert steps_by_name["Install cargo-deny"]["with"]["tool"] == "cargo-deny@0.20.2"


def test_rust_security_handles_missing_lockfiles() -> None:
    """Library crates may resolve a temporary lockfile before auditing."""
    data = _load_workflow()
    steps = data["jobs"]["audit"]["steps"]
    steps_by_name = {step.get("name"): step for step in steps if step.get("name")}

    resolver = steps_by_name["Resolve missing lockfile"]
    assert resolver["if"] == "inputs.generate-lockfile"
    assert "cargo generate-lockfile" in resolver["run"]

    required = steps_by_name["Require Cargo.lock"]["run"]
    assert "Cargo.lock is required for cargo-audit" in required


def test_rust_security_builds_ignore_arguments_safely() -> None:
    """Ignored advisories should be passed through a Bash argument array."""
    data = _load_workflow()
    steps = data["jobs"]["audit"]["steps"]
    audit = next(step for step in steps if step.get("name") == "Audit Rust dependencies")

    assert 'args+=(--ignore "$advisory_id")' in audit["run"]
    assert 'cargo audit "${args[@]}"' in audit["run"]
    assert audit["working-directory"] == "${{ inputs.working-directory }}"


def test_rust_security_cargo_deny_is_opt_in() -> None:
    """cargo-deny should require explicit policy adoption by the consumer."""
    data = _load_workflow()
    steps = data["jobs"]["audit"]["steps"]
    steps_by_name = {step.get("name"): step for step in steps if step.get("name")}

    assert steps_by_name["Validate cargo-deny policy"]["if"] == "inputs.run-cargo-deny"
    assert steps_by_name["Install cargo-deny"]["if"] == "inputs.run-cargo-deny"
    assert steps_by_name["Enforce Rust dependency policy"]["if"] == "inputs.run-cargo-deny"


def test_rust_security_validates_deny_checks() -> None:
    """Only known cargo-deny check names should be accepted."""
    data = _load_workflow()
    steps = data["jobs"]["audit"]["steps"]
    validate = next(
        step for step in steps if step.get("name") == "Validate cargo-deny policy"
    )

    for check in ("advisories", "bans", "licenses", "sources"):
        assert check in validate["run"]

    assert "Unsupported cargo-deny check" in validate["run"]


def test_rust_security_runs_cargo_deny_with_argument_array() -> None:
    """Policy checks should be forwarded without shell interpolation."""
    data = _load_workflow()
    steps = data["jobs"]["audit"]["steps"]
    deny = next(
        step for step in steps if step.get("name") == "Enforce Rust dependency policy"
    )

    assert 'args+=("$check")' in deny["run"]
    assert 'cargo deny --config "$CARGO_DENY_CONFIG" check "${args[@]}"' in deny["run"]
    assert deny["working-directory"] == "${{ inputs.working-directory }}"


def test_rust_security_has_executable_self_test() -> None:
    """Exercise the workflow against the maintained Rust example crate."""
    path = Path(".github/workflows/test-rust-security.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["rust-security-example"]
    assert smoke["uses"] == "./.github/workflows/rust-security.yml"
    assert smoke["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "generate-lockfile": True,
        "run-cargo-deny": True,
        "cargo-deny-config": "deny.toml",
        "cargo-deny-checks": "advisories,bans,licenses,sources",
    }
