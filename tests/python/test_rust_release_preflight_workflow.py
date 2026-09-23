from pathlib import Path
from typing import Any

import yaml


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust release-preflight workflow."""
    path = Path(".github/workflows/rust-release-preflight.yml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _workflow_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Return workflow_call inputs while handling YAML's reserved 'on' token."""
    on_block = data.get("on") or data.get(True)
    return on_block["workflow_call"]["inputs"]


def test_rust_release_preflight_inputs_are_strict_by_default() -> None:
    """Release metadata checks should default to the professional package surface."""
    inputs = _workflow_inputs(_load_workflow())

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["package-name"]["default"] == ""
    assert inputs["locked"]["default"] is False
    assert inputs["require-description"]["default"] is True
    assert inputs["require-repository"]["default"] is True
    assert inputs["require-readme"]["default"] is True
    assert inputs["upload-crate"]["default"] is False
    assert inputs["artifact-retention-days"]["default"] == 7
    assert inputs["use-cache"]["default"] is True


def test_rust_release_preflight_uses_read_only_permissions() -> None:
    """Packaging and metadata validation should not require write permissions."""
    data = _load_workflow()

    assert data["permissions"] == {"contents": "read"}


def test_rust_release_preflight_selects_publishable_package_explicitly() -> None:
    """Workspaces must not accidentally package an arbitrary crate."""
    data = _load_workflow()
    steps = data["jobs"]["preflight"]["steps"]
    metadata = next(
        step for step in steps if step.get("name") == "Validate package metadata"
    )

    assert "multiple publishable workspace packages found" in metadata["run"]
    assert "set package-name explicitly" in metadata["run"]
    assert "publish = false" in metadata["run"]


def test_rust_release_preflight_validates_release_metadata() -> None:
    """Licence and caller-selected metadata requirements should be enforced."""
    data = _load_workflow()
    steps = data["jobs"]["preflight"]["steps"]
    metadata = next(
        step for step in steps if step.get("name") == "Validate package metadata"
    )

    for field in ("license or license-file", "description", "repository", "readme"):
        assert field in metadata["run"]

    assert "package readme does not exist" in metadata["run"]


def test_rust_release_preflight_runs_verified_cargo_package() -> None:
    """The preflight must run cargo package without disabling verification."""
    data = _load_workflow()
    steps = data["jobs"]["preflight"]["steps"]
    package = next(step for step in steps if step.get("name") == "Package crate")

    assert 'args=(-p "$PACKAGE_NAME")' in package["run"]
    assert 'args+=(--locked)' in package["run"]
    assert 'cargo package "${args[@]}"' in package["run"]
    assert "--no-verify" not in package["run"]
    assert "--allow-dirty" not in package["run"]


def test_rust_release_preflight_exposes_resolved_package_outputs() -> None:
    """Callers should be able to reuse the resolved package identity."""
    data = _load_workflow()
    outputs = (data.get("on") or data.get(True))["workflow_call"]["outputs"]

    assert outputs["package-name"]["value"] == "${{ jobs.preflight.outputs.package-name }}"
    assert outputs["package-version"]["value"] == "${{ jobs.preflight.outputs.package-version }}"


def test_rust_release_preflight_upload_is_opt_in() -> None:
    """Generated .crate files should only be retained when requested."""
    data = _load_workflow()
    steps = data["jobs"]["preflight"]["steps"]
    upload = next(step for step in steps if step.get("name") == "Upload crate archive")

    assert upload["if"] == "inputs.upload-crate && success()"
    assert upload["with"]["path"] == "${{ inputs.working-directory }}/target/package/*.crate"
    assert upload["with"]["if-no-files-found"] == "error"


def test_rust_release_preflight_has_executable_self_test() -> None:
    """Exercise metadata validation and cargo package on the maintained example crate."""
    path = Path(".github/workflows/test-rust-release-preflight.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["rust-release-preflight-example"]
    assert smoke["uses"] == "./.github/workflows/rust-release-preflight.yml"
    assert smoke["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "package-name": "rust-crate",
        "locked": False,
        "upload-crate": False,
    }
