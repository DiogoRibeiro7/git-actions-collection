"""node-ci installs with npm, Yarn or pnpm: the package-manager input names it, or package.json's
packageManager field, or the lockfile. It asks that manager for its own cache folder, because
setup-node's `cache` input runs the runner's global Yarn or pnpm, and Yarn 1's `yarn cache dir`
exits 1 in projects that pin Yarn 2+ through packageManager."""

import json
import os
from pathlib import Path
import shutil
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import ActionResult, run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/node-ci.yml"
MANAGER = "steps.manager.outputs.manager"
LOCKFILES = {"npm": "package-lock.json", "yarn": "yarn.lock", "pnpm": "pnpm-lock.yaml"}

posix = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="Requires Node.js")
needs_npm = pytest.mark.skipif(
    shutil.which("node") is None or shutil.which("npm") is None, reason="Requires npm"
)


def _workflow() -> dict[str, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _steps() -> list[dict[str, Any]]:
    return _workflow()["jobs"]["build"]["steps"]


def _step(name: str) -> dict[str, Any]:
    return next(step for step in _steps() if step.get("name") == name)


def _choose(workdir: Path, package_manager: str) -> ActionResult:
    return run_workflow_step(
        WORKFLOW,
        "build",
        "Choose the package manager",
        context={"inputs.package-manager": package_manager},
        workdir=workdir,
    )


def _fake_manager(tmp_path: Path, manager: str, version: str) -> dict[str, str]:
    fakebin = make_fakebin(
        tmp_path,
        {manager: f'if [ "$1" = "--version" ]; then echo {version}; else echo "{manager} $*"; fi'},
    )
    return {"PATH": f"{fakebin}:{os.environ['PATH']}"}


def test_inputs_default_to_detecting_the_package_manager_at_the_root() -> None:
    workflow = _workflow()
    inputs = (workflow.get("on") or workflow[True])["workflow_call"]["inputs"]

    assert inputs["node-version"]["default"] == "24"
    assert inputs["package-manager"]["default"] == "auto"
    assert inputs["working-directory"]["default"] == "."
    assert workflow["jobs"]["build"]["defaults"]["run"] == {
        "shell": "bash",
        "working-directory": "${{ inputs.working-directory }}",
    }


def test_packages_are_cached_after_corepack_not_by_setup_node() -> None:
    steps = _steps()
    names = [step.get("name") for step in steps]
    setup_node = next(s for s in steps if s.get("uses", "").startswith("actions/setup-node@"))
    key = _step("Cache packages")["with"]["key"]

    assert "cache" not in setup_node["with"]
    assert (
        names.index("Choose the package manager")
        < names.index("Enable Corepack")
        < names.index("Locate the package cache")
        < names.index("Cache packages")
        < names.index("Install dependencies")
    )
    assert _step("Enable Corepack")["if"] == f"{MANAGER} != 'npm'"
    assert key.startswith("${{ steps.manager.outputs.manager }}-${{ runner.os }}-")
    assert "steps.manager.outputs.lockfile" in key


def test_the_summary_runs_last_even_after_a_failure_and_from_the_checkout() -> None:
    steps = _steps()
    summary = _step("Summary")

    assert steps[-1].get("name") == "Summary"
    assert summary["if"] == "always()"
    assert summary["working-directory"] == "${{ github.workspace }}"
    assert summary["env"]["STEPS"] == "${{ toJSON(steps) }}"
    assert {step.get("id") for step in steps} >= {"node", "manager", "install", "lint", "tests"}


@posix
@needs_node
@pytest.mark.parametrize(
    ("manifest", "files", "expected"),
    [
        (None, [], "npm"),
        ({}, [], "npm"),
        ({}, ["package-lock.json"], "npm"),
        ({}, ["yarn.lock"], "yarn"),
        ({}, ["pnpm-lock.yaml"], "pnpm"),
        ({}, ["yarn.lock", "pnpm-lock.yaml"], "pnpm"),
        ({"packageManager": "yarn@4.18.1"}, ["package-lock.json"], "yarn"),
        ({"packageManager": "pnpm@12.6.0+sha512.0123abcd"}, [], "pnpm"),
        ({"packageManager": "npm@11.6.2"}, ["yarn.lock"], "npm"),
    ],
)
def test_auto_reads_package_json_then_the_lockfile(
    tmp_path: Path, manifest: dict[str, str] | None, files: list[str], expected: str
) -> None:
    if manifest is not None:
        (tmp_path / "package.json").write_text(json.dumps({"name": "fixture", **manifest}))
    for name in files:
        (tmp_path / name).touch()

    result = _choose(tmp_path, "auto")

    assert result.code == 0, result.stderr
    assert result.outputs == {"manager": expected, "lockfile": LOCKFILES[expected]}


@posix
@pytest.mark.parametrize("manager", ["npm", "yarn", "pnpm"])
def test_the_input_overrides_detection(tmp_path: Path, manager: str) -> None:
    (tmp_path / "package.json").write_text(json.dumps({"packageManager": "bun@1.3.0"}))
    (tmp_path / "pnpm-lock.yaml").touch()

    result = _choose(tmp_path, manager)

    assert result.code == 0, result.stderr
    assert result.outputs == {"manager": manager, "lockfile": LOCKFILES[manager]}


@posix
@pytest.mark.parametrize("manager", ["bun", "Yarn", ""])
def test_an_unsupported_package_manager_fails(tmp_path: Path, manager: str) -> None:
    result = _choose(tmp_path, manager)

    assert result.code == 1
    assert f"supports npm, yarn and pnpm, not '{manager}'" in result.stdout
    assert result.outputs == {}


@posix
@needs_node
def test_an_unsupported_declared_package_manager_fails(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(json.dumps({"packageManager": "bun@1.3.0"}))

    result = _choose(tmp_path, "auto")

    assert result.code == 1
    assert "not 'bun'" in result.stdout


@posix
@pytest.mark.parametrize(
    ("manager", "version", "expected"),
    [
        ("npm", "11.6.2", "npm config get cache"),
        ("pnpm", "12.6.0", "pnpm store path"),
        ("yarn", "1.22.22", "yarn cache dir"),
        ("yarn", "4.18.1", "yarn config get cacheFolder"),
    ],
)
def test_the_projects_own_manager_names_the_cache(
    tmp_path: Path, manager: str, version: str, expected: str
) -> None:
    result = run_workflow_step(
        WORKFLOW,
        "build",
        "Locate the package cache",
        context={MANAGER: manager},
        env=_fake_manager(tmp_path, manager, version),
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.outputs["dir"] == expected


@posix
@pytest.mark.parametrize(
    ("manager", "version", "expected"),
    [
        ("npm", "11.6.2", "npm ci"),
        ("pnpm", "12.6.0", "pnpm install --frozen-lockfile"),
        ("yarn", "1.22.22", "yarn install --frozen-lockfile"),
        ("yarn", "4.18.1", "yarn install --immutable"),
    ],
)
def test_dependencies_install_from_the_lockfile_without_changing_it(
    tmp_path: Path, manager: str, version: str, expected: str
) -> None:
    result = run_workflow_step(
        WORKFLOW,
        "build",
        "Install dependencies",
        context={MANAGER: manager},
        env=_fake_manager(tmp_path, manager, version),
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.stdout.splitlines() == [expected]
    assert result.outputs == {"command": expected}


@posix
@pytest.mark.parametrize("manager", ["npm", "yarn", "pnpm"])
@pytest.mark.parametrize(("step", "script"), [("Run lint", "lint"), ("Run tests", "test")])
def test_lint_and_tests_run_the_package_scripts(
    tmp_path: Path, manager: str, step: str, script: str
) -> None:
    result = run_workflow_step(
        WORKFLOW,
        "build",
        step,
        context={MANAGER: manager},
        env=_fake_manager(tmp_path, manager, "1.0.0"),
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.stdout.splitlines() == [f"{manager} run {script}"]


@posix
@needs_npm
@pytest.mark.parametrize(
    ("lockfile", "message"),
    [
        (None, "can only install with an existing package-lock.json"),
        (
            {
                "name": "fixture",
                "version": "1.0.0",
                "lockfileVersion": 3,
                "packages": {"": {"name": "fixture", "version": "1.0.0"}},
            },
            "Missing: local@1.0.0 from lock file",
        ),
    ],
)
def test_npm_install_fails_without_a_lockfile_that_matches_package_json(
    tmp_path: Path, lockfile: dict[str, Any] | None, message: str
) -> None:
    """`npm ci` refuses instead of resolving versions the lockfile does not record.

    The dependency is a local directory, so npm needs no registry, and the npm cache is empty
    and offline, so the result does not depend on what this machine has downloaded before.
    """
    (tmp_path / "local").mkdir()
    (tmp_path / "local" / "package.json").write_text(
        json.dumps({"name": "local", "version": "1.0.0"})
    )
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "fixture", "version": "1.0.0", "dependencies": {"local": "file:local"}})
    )
    if lockfile is not None:
        (tmp_path / "package-lock.json").write_text(json.dumps(lockfile))

    result = run_workflow_step(
        WORKFLOW,
        "build",
        "Install dependencies",
        context={MANAGER: "npm"},
        env={"npm_config_offline": "true", "npm_config_cache": str(tmp_path / "npm-cache")},
        workdir=tmp_path,
    )

    assert result.code != 0
    assert message in result.stderr
    assert not (tmp_path / "node_modules").exists()


@posix
@needs_npm
@pytest.mark.parametrize(("step", "script"), [("Run lint", "lint"), ("Run tests", "test")])
def test_a_failing_lint_or_test_script_fails_the_job(
    tmp_path: Path, step: str, script: str
) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "name": "fixture",
                "scripts": {script: "node -e \"console.error('failing'); process.exit(3)\""},
            }
        )
    )

    result = run_workflow_step(WORKFLOW, "build", step, context={MANAGER: "npm"}, workdir=tmp_path)

    assert result.code == 3
    assert "failing" in result.stderr


def _summary(tmp_path: Path, steps: dict[str, Any] | str, **inputs: str) -> ActionResult:
    """Run the Summary step; *steps* is the steps context, or raw text in its place."""
    context = {
        "toJSON(steps)": steps if isinstance(steps, str) else json.dumps(steps),
        "inputs.node-version": "24",
        "inputs.package-manager": "auto",
        "inputs.working-directory": ".",
        "matrix.os": "ubuntu-latest",
        "github.workspace": str(tmp_path),
    }
    context.update({f"inputs.{name.replace('_', '-')}": value for name, value in inputs.items()})
    return run_workflow_step(WORKFLOW, "build", "Summary", context=context, workdir=tmp_path)


def _ran(outcome: str, **outputs: str) -> dict[str, Any]:
    return {"outcome": outcome, "conclusion": outcome, "outputs": outputs}


@posix
@needs_node
def test_the_summary_lists_each_command_and_its_result(tmp_path: Path) -> None:
    result = _summary(
        tmp_path,
        {
            "node": _ran("success"),
            "manager": _ran("success", manager="npm", lockfile="package-lock.json"),
            "install": _ran("success", command="npm ci"),
            "lint": _ran("success"),
            "tests": _ran("success"),
        },
    )

    assert result.code == 0, result.stderr
    lines = result.summary.splitlines()
    assert lines[0] == "## Node CI on ubuntu-latest"
    assert lines[2].startswith("Node.js v") and lines[2].endswith(" · package manager npm")
    assert lines[4:] == [
        "| Step | Command | Result |",
        "| --- | --- | --- |",
        "| Install | `npm ci` | ✅ Passed |",
        "| Lint | `npm run lint` | ✅ Passed |",
        "| Tests | `npm run test` | ✅ Passed |",
    ]


@posix
@needs_node
def test_the_summary_shows_which_step_failed_and_where(tmp_path: Path) -> None:
    result = _summary(
        tmp_path,
        {
            "node": _ran("success"),
            "manager": _ran("success", manager="yarn", lockfile="yarn.lock"),
            "install": _ran("success", command="yarn install --immutable"),
            "lint": _ran("failure"),
            "tests": _ran("skipped"),
        },
        working_directory="packages/web|app",
    )

    assert result.code == 0, result.stderr
    assert r"package manager yarn · directory `packages/web\|app`" in result.summary
    assert "| Lint | `yarn run lint` | ❌ Failed |" in result.summary
    assert "| Tests | `yarn run test` | Skipped |" in result.summary


@posix
@needs_node
def test_the_summary_explains_a_job_that_stopped_before_installing(tmp_path: Path) -> None:
    result = _summary(
        tmp_path,
        {"node": _ran("failure"), "manager": _ran("failure")},
        node_version="99",
        package_manager="bun",
    )

    assert result.code == 0, result.stderr
    assert "Node.js 99 (not set up) · package manager not chosen" in result.summary
    assert "| Package manager | `package-manager: bun` | ❌ Failed |" in result.summary
    assert "| Install | — | Not run |" in result.summary
    assert "| Tests | — | Not run |" in result.summary


@posix
@needs_node
def test_a_broken_summary_warns_instead_of_failing_the_job(tmp_path: Path) -> None:
    result = _summary(tmp_path, "not json")

    assert result.code == 0
    assert "::warning title=Node CI summary::Could not write the summary" in result.stdout
    assert result.summary == ""
