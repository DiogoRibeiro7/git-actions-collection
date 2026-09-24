import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

WORKFLOW = Path(".github/workflows/rust-release-preflight.yml")
WORKSPACE_EXAMPLE = Path("examples/rust-workspace")
CARGO_VERSION = "cargo 1.98.1 (797e8a9bc 2026-08-05)"


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust release-preflight workflow."""
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _workflow_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Return workflow_call inputs while handling YAML's reserved 'on' token."""
    on_block = data.get("on") or data.get(True)
    return on_block["workflow_call"]["inputs"]


def _step(name: str) -> dict[str, Any]:
    steps = _load_workflow()["jobs"]["preflight"]["steps"]
    return next(step for step in steps if step.get("name") == name)


def test_rust_release_preflight_inputs_are_strict_by_default() -> None:
    """Release metadata checks should default to the professional package surface."""
    inputs = _workflow_inputs(_load_workflow())

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["package-name"]["default"] == ""
    assert inputs["packages"]["default"] == ""
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


def test_rust_release_preflight_runs_verified_cargo_package() -> None:
    """The preflight must package the whole selection without disabling verification."""
    package = _step("Package crate")

    assert 'args+=(-p "$name")' in package["run"]
    assert 'args+=(--locked)' in package["run"]
    assert 'cargo package "${args[@]}"' in package["run"]
    for forbidden in ("--no-verify", "--allow-dirty", "--workspace"):
        assert forbidden not in package["run"]


def test_rust_release_preflight_reads_archives_from_cargo_target_directory() -> None:
    """Workspace members build into the workspace-root target directory."""
    verify = _step("Verify package archive")

    assert "working-directory" not in verify
    assert 'crate_path="$TARGET_DIRECTORY/package/$crate_file"' in verify["run"]
    assert verify["env"]["TARGET_DIRECTORY"] == "${{ steps.metadata.outputs.target-directory }}"


def test_rust_release_preflight_exposes_resolved_package_outputs() -> None:
    """Callers should be able to reuse the resolved package identity and plan."""
    data = _load_workflow()
    outputs = (data.get("on") or data.get(True))["workflow_call"]["outputs"]

    for name in ("package-name", "package-version", "packages", "artifact-name"):
        assert outputs[name]["value"] == f"${{{{ jobs.preflight.outputs.{name} }}}}"


def test_rust_release_preflight_upload_is_opt_in_and_selection_only() -> None:
    """Only the selected packages' archives are retained, and only on request."""
    upload = _step("Upload crate archive")

    assert upload["if"] == "inputs.upload-crate && success()"
    assert upload["with"]["name"] == "${{ steps.metadata.outputs.artifact-name }}"
    assert upload["with"]["path"] == "${{ runner.temp }}/rust-release-crates/*.crate"
    assert upload["with"]["if-no-files-found"] == "error"


def test_rust_release_preflight_has_executable_self_tests() -> None:
    """Exercise a single crate and an ordered workspace selection end to end."""
    path = Path(".github/workflows/test-rust-release-preflight.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    single = data["jobs"]["rust-release-preflight-example"]
    assert single["uses"] == "./.github/workflows/rust-release-preflight.yml"
    assert single["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "package-name": "rust-crate",
        "locked": False,
        "upload-crate": False,
    }

    workspace = data["jobs"]["rust-release-preflight-workspace"]
    assert workspace["uses"] == "./.github/workflows/rust-release-preflight.yml"
    assert workspace["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-workspace/crates/cli",
        "packages": "gac-example-core gac-example-cli",
        "locked": False,
        "upload-crate": True,
        "artifact-retention-days": 1,
    }

    verify = data["jobs"]["verify-workspace-plan"]
    assert verify["needs"] == "rust-release-preflight-workspace"
    assert "gac-example-core gac-example-cli" in verify["steps"][1]["run"]


# Executable coverage of the package-resolution script embedded in the workflow.


def _resolution_script() -> str:
    match = re.search(
        r"<<'PY'\n(.*?)\nPY\b", _step("Validate package metadata")["run"], re.DOTALL
    )
    assert match
    return match.group(1)


def _dependency(name: str, root: Path, kind: str | None = None) -> dict[str, Any]:
    return {"name": name, "kind": kind, "path": str(root / name)}


def _package(
    root: Path,
    name: str,
    *,
    version: str = "0.1.0",
    publish: list[str] | None = None,
    dependencies: tuple[dict[str, Any], ...] = (),
    readme: str | None = "README.md",
    **fields: Any,
) -> dict[str, Any]:
    """Build a cargo-metadata package whose README lives beside its manifest."""
    manifest_dir = root / name
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    package = {
        "id": f"path+file:///{name}#{version}",
        "name": name,
        "version": version,
        "publish": publish,
        "license": "MIT",
        "description": f"{name} crate",
        "repository": "https://example.test/repo",
        "readme": readme,
        "manifest_path": str(manifest_dir / "Cargo.toml"),
        "dependencies": list(dependencies),
    }
    package.update(fields)
    return package


def _resolve(
    tmp_path: Path,
    packages: list[dict[str, Any]],
    *,
    package_name: str = "",
    package_list: str = "",
    cargo_version: str = CARGO_VERSION,
    metadata: dict[str, Any] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, str], str]:
    """Run the resolution script from an unrelated directory, like a member crate."""
    if metadata is None:
        metadata = {
            "packages": packages,
            "workspace_members": [package["id"] for package in packages],
            "target_directory": str(tmp_path / "target"),
        }
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    output = tmp_path / "github-output"
    summary = tmp_path / "step-summary"
    output.write_text("", encoding="utf-8")
    summary.write_text("", encoding="utf-8")
    cwd = tmp_path / "cwd"
    cwd.mkdir(exist_ok=True)

    result = subprocess.run(
        [
            sys.executable,
            "-",
            str(metadata_path),
            package_name,
            package_list,
            "true",
            "true",
            "true",
            cargo_version,
            str(output),
            str(summary),
        ],
        input=_resolution_script(),
        text=True,
        capture_output=True,
        cwd=cwd,
        check=False,
    )
    outputs = dict(
        line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines() if line
    )
    return result, outputs, summary.read_text(encoding="utf-8")


def test_single_publishable_crate_is_selected_implicitly(tmp_path: Path) -> None:
    packages = [_package(tmp_path, "core"), _package(tmp_path, "tools", publish=[])]
    result, outputs, summary = _resolve(tmp_path, packages)

    assert result.returncode == 0, result.stderr
    assert outputs == {
        "package-name": "core",
        "package-version": "0.1.0",
        "packages": "core",
        "crate-files": "core-0.1.0.crate",
        "target-directory": str(tmp_path / "target"),
        "artifact-name": "rust-crate-core-0.1.0",
    }
    assert "| 1 | `core` | `0.1.0` |" in summary


def test_multiple_publishable_crates_require_explicit_selection(tmp_path: Path) -> None:
    packages = [_package(tmp_path, "core"), _package(tmp_path, "cli")]
    result, outputs, _ = _resolve(tmp_path, packages)

    assert result.returncode != 0
    assert "multiple publishable workspace packages found" in result.stderr
    assert "set package-name or packages explicitly: cli, core" in result.stderr
    assert outputs == {}


def test_explicit_package_name_selects_one_workspace_crate(tmp_path: Path) -> None:
    packages = [_package(tmp_path, "core"), _package(tmp_path, "cli")]
    result, outputs, _ = _resolve(tmp_path, packages, package_name="cli")

    assert result.returncode == 0, result.stderr
    assert outputs["package-name"] == "cli"
    assert outputs["packages"] == "cli"


def test_no_publishable_crates_is_an_error(tmp_path: Path) -> None:
    result, _, _ = _resolve(tmp_path, [_package(tmp_path, "tools", publish=[])])

    assert result.returncode != 0
    assert "no publishable workspace packages found" in result.stderr


@pytest.mark.parametrize(
    ("publish", "message"),
    [([], "has publish = false"), (["internal-registry"], "may only be published to internal-registry")],
)
def test_explicitly_selected_unpublishable_crate_is_rejected(
    tmp_path: Path, publish: list[str], message: str
) -> None:
    packages = [_package(tmp_path, "core"), _package(tmp_path, "tools", publish=publish)]
    result, _, _ = _resolve(tmp_path, packages, package_list="core tools")

    assert result.returncode != 0
    assert f"package 'tools' {message}" in result.stderr


def test_crates_io_listed_in_publish_registries_is_publishable(tmp_path: Path) -> None:
    packages = [_package(tmp_path, "core", publish=["crates-io", "mirror"])]
    result, outputs, _ = _resolve(tmp_path, packages, package_name="core")

    assert result.returncode == 0, result.stderr
    assert outputs["packages"] == "core"


@pytest.mark.parametrize(
    ("package_name", "package_list", "message"),
    [
        ("missing", "", "not workspace packages: missing; available: cli, core"),
        ("", "core, nope", "not workspace packages: nope; available: cli, core"),
        ("", "core core", "packages lists duplicates: core"),
        ("core", "cli", "set either package-name or packages, not both"),
    ],
)
def test_invalid_package_selection_is_rejected(
    tmp_path: Path, package_name: str, package_list: str, message: str
) -> None:
    packages = [_package(tmp_path, "core"), _package(tmp_path, "cli")]
    result, outputs, _ = _resolve(
        tmp_path, packages, package_name=package_name, package_list=package_list
    )

    assert result.returncode != 0
    assert message in result.stderr
    assert outputs == {}


@pytest.mark.parametrize("package_list", ["core cli", "core,cli", "core, cli", "\ncore\ncli\n"])
def test_ordered_workspace_selection_is_accepted(tmp_path: Path, package_list: str) -> None:
    core = _package(tmp_path, "core")
    cli = _package(tmp_path, "cli", dependencies=(_dependency("core", tmp_path),))
    result, outputs, summary = _resolve(tmp_path, [cli, core], package_list=package_list)

    assert result.returncode == 0, result.stderr
    assert outputs["packages"] == "core cli"
    assert outputs["crate-files"] == "core-0.1.0.crate cli-0.1.0.crate"
    assert outputs["artifact-name"] == "rust-crates-core-0.1.0-and-1-more"
    assert "package-name" not in outputs
    assert summary.index("`core`") < summary.index("`cli`")


def test_dependents_listed_before_dependencies_are_rejected(tmp_path: Path) -> None:
    core = _package(tmp_path, "core")
    cli = _package(tmp_path, "cli", dependencies=(_dependency("core", tmp_path),))
    result, outputs, _ = _resolve(tmp_path, [core, cli], package_list="cli core")

    assert result.returncode != 0
    assert "packages must list 'core' before 'cli', which depends on it" in result.stderr
    assert outputs == {}


@pytest.mark.parametrize("kind", [None, "build"])
def test_dependency_on_unpublishable_workspace_crate_is_rejected(
    tmp_path: Path, kind: str | None
) -> None:
    tools = _package(tmp_path, "tools", publish=[])
    cli = _package(tmp_path, "cli", dependencies=(_dependency("tools", tmp_path, kind),))
    result, _, _ = _resolve(tmp_path, [tools, cli], package_name="cli")

    assert result.returncode != 0
    assert "package 'cli' depends on workspace package 'tools', which cannot be published" in (
        result.stderr
    )


def test_dev_dependency_on_unpublishable_workspace_crate_is_allowed(tmp_path: Path) -> None:
    """Cargo strips path-only dev-dependencies from published manifests."""
    tools = _package(tmp_path, "tools", publish=[])
    cli = _package(tmp_path, "cli", dependencies=(_dependency("tools", tmp_path, "dev"),))
    result, outputs, _ = _resolve(tmp_path, [tools, cli], package_name="cli")

    assert result.returncode == 0, result.stderr
    assert outputs["packages"] == "cli"


def test_unselected_workspace_dependency_is_reported(tmp_path: Path) -> None:
    """Releasing a dependent alone relies on its dependency already being on crates.io."""
    core = _package(tmp_path, "core")
    cli = _package(tmp_path, "cli", dependencies=(_dependency("core", tmp_path),))
    result, outputs, _ = _resolve(tmp_path, [core, cli], package_name="cli")

    assert result.returncode == 0, result.stderr
    assert "::notice::cli depends on workspace package core, which is not selected" in (
        result.stdout
    )
    assert outputs["packages"] == "cli"


def test_registry_dependency_sharing_a_workspace_name_is_ignored(tmp_path: Path) -> None:
    """Only path dependencies on workspace members affect the publication plan."""
    tools = _package(tmp_path, "tools", publish=[])
    cli = _package(tmp_path, "cli", dependencies=({"name": "tools", "kind": None},))
    result, _, _ = _resolve(tmp_path, [tools, cli], package_name="cli")

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("cargo_version", "package_list", "ok"),
    [
        ("cargo 1.89.0 (c24e10642 2025-06-23)", "core cli", False),
        ("cargo 1.90.0 (840b83a10 2025-07-30)", "core cli", True),
        ("cargo 1.89.0 (c24e10642 2025-06-23)", "core", True),
    ],
)
def test_multi_package_selection_requires_modern_cargo(
    tmp_path: Path, cargo_version: str, package_list: str, ok: bool
) -> None:
    packages = [_package(tmp_path, "core"), _package(tmp_path, "cli")]
    result, _, _ = _resolve(
        tmp_path, packages, package_list=package_list, cargo_version=cargo_version
    )

    assert (result.returncode == 0) is ok, result.stderr
    if not ok:
        assert "requires Cargo 1.90 or newer" in result.stderr


def test_release_metadata_is_required_for_every_selected_crate(tmp_path: Path) -> None:
    core = _package(tmp_path, "core")
    cli = _package(tmp_path, "cli", description=None, license=None)
    result, _, _ = _resolve(tmp_path, [core, cli], package_list="core cli")

    assert result.returncode != 0
    assert "package 'cli' is missing release metadata: license or license-file, description" in (
        result.stderr
    )


def test_readme_is_resolved_beside_each_member_manifest(tmp_path: Path) -> None:
    """A member README must be found even when the working directory is elsewhere."""
    packages = [_package(tmp_path, "core")]
    result, _, _ = _resolve(tmp_path, packages)
    assert result.returncode == 0, result.stderr

    (tmp_path / "core" / "README.md").unlink()
    result, _, _ = _resolve(tmp_path, packages)
    assert result.returncode != 0
    assert "package readme does not exist" in result.stderr


@pytest.mark.skipif(shutil.which("cargo") is None, reason="cargo is not installed")
@pytest.mark.parametrize(
    ("package_list", "message"),
    [
        ("gac-example-core gac-example-cli", None),
        ("gac-example-cli gac-example-core", "must list 'gac-example-core' before 'gac-example-cli'"),
        ("gac-example-core gac-example-internal", "'gac-example-internal' has publish = false"),
    ],
)
def test_workspace_example_metadata_drives_the_plan(
    tmp_path: Path, package_list: str, message: str | None
) -> None:
    """The committed workspace fixture really has the relationships the plan relies on."""
    metadata = json.loads(
        subprocess.run(
            ["cargo", "metadata", "--no-deps", "--format-version", "1", "--offline"],
            cwd=WORKSPACE_EXAMPLE,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
    )
    result, outputs, _ = _resolve(tmp_path, [], package_list=package_list, metadata=metadata)

    if message is None:
        assert result.returncode == 0, result.stderr
        assert outputs["packages"] == "gac-example-core gac-example-cli"
    else:
        assert result.returncode != 0
        assert message in result.stderr
