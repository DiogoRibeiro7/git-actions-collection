import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(".github/workflows/rust-publish.yml")


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust publish workflow."""
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _workflow_call(data: dict[str, Any]) -> dict[str, Any]:
    """Return the workflow_call block while handling YAML's reserved 'on' token."""
    on_block = data.get("on") or data.get(True)
    return on_block["workflow_call"]


def _publish_step(name: str) -> dict[str, Any]:
    steps = _load_workflow()["jobs"]["publish"]["steps"]
    return next(step for step in steps if step.get("name") == name)


def test_rust_publish_defaults_to_dry_run() -> None:
    """Publishing must require an explicit opt-in to mutate crates.io."""
    inputs = _workflow_call(_load_workflow())["inputs"]

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["package-name"]["default"] == ""
    assert inputs["packages"]["default"] == ""
    assert inputs["locked"]["default"] is False
    assert inputs["dry-run"]["default"] is True
    assert inputs["release-environment"]["default"] == "release"


def test_rust_publish_verifies_the_plan_with_the_release_preflight() -> None:
    """Every selected crate is verified read-only before the protected publish job."""
    data = _load_workflow()
    preflight = data["jobs"]["preflight"]

    assert preflight["uses"] == "./.github/workflows/rust-release-preflight.yml"
    assert "if" not in preflight
    assert "permissions" not in preflight
    assert data["permissions"] == {"contents": "read"}
    assert preflight["with"] == {
        "rust-toolchain": "${{ inputs.rust-toolchain }}",
        "working-directory": "${{ inputs.working-directory }}",
        "package-name": "${{ inputs.package-name }}",
        "packages": "${{ inputs.packages }}",
        "locked": "${{ inputs.locked }}",
        "require-description": True,
        "require-repository": False,
        "require-readme": False,
        "use-cache": False,
    }


def test_rust_publish_exposes_the_verified_plan() -> None:
    outputs = _workflow_call(_load_workflow())["outputs"]

    assert outputs["packages"]["value"] == "${{ jobs.preflight.outputs.packages }}"


def test_rust_publish_live_job_requires_oidc_and_environment() -> None:
    """Live publishing must run through an environment with OIDC enabled."""
    job = _load_workflow()["jobs"]["publish"]

    assert job["needs"] == "preflight"
    assert job["if"] == "${{ !inputs.dry-run }}"
    assert job["environment"] == "${{ inputs.release-environment }}"
    assert job["permissions"] == {
        "contents": "read",
        "id-token": "write",
    }


def test_rust_publish_uses_pinned_trusted_publishing_action() -> None:
    """crates.io authentication should use the official pinned OIDC action."""
    auth = _publish_step("Authenticate to crates.io")

    assert auth["id"] == "crates-io-auth"
    assert (
        auth["uses"]
        == "rust-lang/crates-io-auth-action@4920f0933d6c80323414a03df1731d6678d52a1b"
    )


def test_rust_publish_does_not_support_long_lived_token_secrets() -> None:
    """The workflow should only consume the short-lived OIDC token output."""
    rendered = WORKFLOW.read_text(encoding="utf-8")

    assert "secrets." not in rendered
    assert "CRATES_IO_TOKEN" not in rendered
    assert "CARGO_REGISTRY_TOKEN" in rendered
    assert "${{ steps.crates-io-auth.outputs.token }}" in rendered


def test_rust_publish_blocks_unsafe_live_events() -> None:
    """Only releases, manual dispatches, and tag pushes may publish."""
    validate = _publish_step("Validate live publication context")

    assert "release|workflow_dispatch" in validate["run"]
    assert 'refs/tags/*' in validate["run"]
    assert "Live crates.io publication is blocked for event" in validate["run"]


def test_rust_publish_publishes_only_the_verified_plan() -> None:
    """The live job must publish the preflight's packages, never an implicit workspace."""
    publish = _publish_step("Publish crate")

    assert publish["env"]["PACKAGES"] == "${{ needs.preflight.outputs.packages }}"
    assert "inputs.package-name" not in str(publish)
    assert "inputs.packages" not in str(publish)
    assert 'cargo publish "${args[@]}"' in publish["run"]
    for forbidden in ("--workspace", "--no-verify", "--allow-dirty"):
        assert forbidden not in WORKFLOW.read_text(encoding="utf-8")


def test_rust_publish_has_executable_dry_run_self_tests() -> None:
    """Exercise single-crate and ordered workspace plans without uploading."""
    path = Path(".github/workflows/test-rust-publish.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    single = data["jobs"]["rust-publish-dry-run"]
    assert single["uses"] == "./.github/workflows/rust-publish.yml"
    # The skipped live job's grant must be allowed or the run fails at startup.
    assert single["permissions"] == {"contents": "read", "id-token": "write"}
    assert single["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "package-name": "rust-crate",
        "locked": False,
        "dry-run": True,
    }

    workspace = data["jobs"]["rust-publish-workspace-dry-run"]
    assert workspace["uses"] == "./.github/workflows/rust-publish.yml"
    assert workspace["permissions"] == {"contents": "read", "id-token": "write"}
    assert workspace["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-workspace",
        "packages": "gac-example-core, gac-example-cli",
        "locked": False,
        "dry-run": True,
    }


posix_only = pytest.mark.skipif(os.name != "posix", reason="Fake runner requires bash (Linux CI)")


def _run_publish_step(tmp_path: Path, step_name: str, context: dict[str, str]) -> Any:
    log = tmp_path / "cargo.log"
    fakebin = make_fakebin(tmp_path, {"cargo": f'printf "%s\\n" "$*" >> "{log}"'})
    (tmp_path / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
    result = run_workflow_step(
        WORKFLOW,
        "publish",
        step_name,
        context,
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )
    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    return result, calls


@posix_only
@pytest.mark.parametrize(
    ("packages", "locked", "expected"),
    [
        ("rust-crate", "false", "publish -p rust-crate"),
        (
            "gac-example-core gac-example-cli",
            "true",
            "publish -p gac-example-core -p gac-example-cli --locked",
        ),
    ],
)
def test_live_publish_passes_each_planned_package(
    tmp_path: Path, packages: str, locked: str, expected: str
) -> None:
    result, calls = _run_publish_step(
        tmp_path,
        "Publish crate",
        {
            "inputs.working-directory": ".",
            "needs.preflight.outputs.packages": packages,
            "inputs.locked": locked,
            "steps.crates-io-auth.outputs.token": "short-lived-token",
        },
    )

    assert result.code == 0, result.stderr
    assert calls == [expected]


@posix_only
def test_live_publish_refuses_an_empty_plan(tmp_path: Path) -> None:
    result, _ = _run_publish_step(
        tmp_path,
        "Validate live publication context",
        {
            "inputs.working-directory": ".",
            "github.event_name": "push",
            "github.ref": "refs/tags/v1.0.0",
            "inputs.release-environment": "release",
            "needs.preflight.outputs.packages": "",
        },
    )

    assert result.code != 0
    assert "The preflight did not resolve any packages to publish" in result.stderr
