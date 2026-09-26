"""Run individual Rust workflow steps against tiny Cargo projects or stubbed tools.

Steps receive their real input defaults, so a test only states what differs
from a default consumer call.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import ActionResult, run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOWS = Path(".github/workflows")
FEEDBACK_SETUP = "Set up run feedback"


def require_rust_tools(*subcommands: str) -> None:
    """Skip locally, but fail in CI, when cargo or a cargo subcommand is missing."""
    missing: list[str] = []
    if shutil.which("cargo") is None:
        missing.append("cargo")
    else:
        for subcommand in subcommands:
            probe = subprocess.run(
                ["cargo", subcommand, "--version"], capture_output=True, check=False
            )
            if probe.returncode != 0:
                missing.append(f"cargo {subcommand}")
    if missing:
        message = "missing Rust tooling: " + ", ".join(missing)
        if os.environ.get("CI") == "true":
            pytest.fail(message)
        pytest.skip(message)


def write_crate(
    root: Path, lib: str, *, features: Mapping[str, list[str]] | None = None
) -> Path:
    """Create a dependency-free library crate with a generated Cargo.lock."""
    manifest = '[package]\nname = "fixture"\nversion = "0.1.0"\nedition = "2021"\n'
    if features:
        manifest += "\n[features]\n"
        for name, enables in features.items():
            # A JSON list of strings is also a valid TOML array.
            manifest += f"{name} = {json.dumps(enables)}\n"
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "Cargo.toml").write_text(manifest, encoding="utf-8")
    (root / "src" / "lib.rs").write_text(lib, encoding="utf-8")
    subprocess.run(
        ["cargo", "generate-lockfile", "--offline"], cwd=root, capture_output=True, check=True
    )
    return root


def _render(value: Any) -> str:
    """Render an input default the way GitHub substitutes it into expressions."""
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    return str(value)


def run_step(
    workflow: str,
    job: str,
    step_name: str,
    workdir: Path,
    inputs: Mapping[str, Any] | None = None,
    stubs: Mapping[str, str] | None = None,
    context: Mapping[str, str] | None = None,
) -> ActionResult:
    """Run one step with default inputs, optional overrides, and optional tool stubs.

    *context* supplies expressions other than inputs, such as ``toJSON(steps)``.
    """
    path = WORKFLOWS / workflow
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    declared = (data.get("on") or data.get(True))["workflow_call"]["inputs"]
    values = {name: spec.get("default") for name, spec in declared.items()}
    values["working-directory"] = "."
    for name, value in (inputs or {}).items():
        assert name in declared, f"{workflow} has no input {name!r}"
        values[name] = value

    step = next(item for item in data["jobs"][job]["steps"] if item.get("name") == step_name)
    expressions = {
        expression: _render(values[expression.removeprefix("inputs.")])
        for expression in re.findall(r"\$\{\{\s*(inputs\.[\w-]+)\s*\}\}", yaml.safe_dump(step))
    }
    expressions.update(context or {})

    # Gates pipe cargo through a script an earlier step writes to RUNNER_TEMP, and annotate
    # files relative to the checkout, which is the fixture's parent directory here.
    runner_temp = workdir.parent / f"{workdir.name}-runner-temp"
    runner_temp.mkdir(exist_ok=True)
    env: dict[str, str] = {"RUNNER_TEMP": str(runner_temp), "GITHUB_WORKSPACE": str(workdir.parent)}
    if stubs:
        fakebin = make_fakebin(workdir.parent / f"{workdir.name}-bin", dict(stubs))
        env["PATH"] = f"{fakebin}:{os.environ['PATH']}"
    if step_name != FEEDBACK_SETUP and "rust_feedback.py" in str(step.get("run")):
        setup = run_workflow_step(path, job, FEEDBACK_SETUP, {}, env=env, workdir=workdir)
        assert setup.code == 0, setup.stderr
    return run_workflow_step(path, job, step_name, expressions, env=env, workdir=workdir)


def cargo_stub(log: Path, exit_code: int = 0) -> dict[str, str]:
    """A cargo stand-in that records its arguments, for tools absent from CI images."""
    return {"cargo": f'printf "%s\\n" "$*" >> "{log}"\nexit {exit_code}'}


# Rust sources that each break exactly one gate; CLEAN_LIB passes all of them.
CLEAN_LIB = """\
//! Fixture crate.

/// Adds two numbers.
pub fn add(left: u32, right: u32) -> u32 {
    left + right
}

#[cfg(test)]
mod tests {
    #[test]
    fn adds() {
        assert_eq!(super::add(2, 2), 4);
    }
}
"""

UNFORMATTED_LIB = CLEAN_LIB.replace(
    "pub fn add(left: u32, right: u32) -> u32 {\n    left + right\n}",
    "pub fn add(left:u32,right:u32)->u32{left+right}",
)

LIB_CLIPPY_WARNING = CLEAN_LIB.replace("    left + right\n", "    return left + right;\n")

TEST_ONLY_CLIPPY_WARNING = CLEAN_LIB.replace(
    "        assert_eq!(super::add(2, 2), 4);\n",
    "        assert_eq!(super::add(2, 2), 4);\n        return;\n",
)

FAILING_TEST_LIB = CLEAN_LIB.replace("super::add(2, 2), 4", "super::add(2, 2), 5")

COMPILE_ERROR_LIB = CLEAN_LIB.replace("    left + right\n", "    left + missing\n")

BROKEN_DOC_LINK_LIB = CLEAN_LIB.replace(
    "/// Adds two numbers.", "/// Adds two numbers; see [`Missing`]."
)

FEATURE_GATED_LIB = CLEAN_LIB + """
#[cfg(not(feature = "extra"))]
compile_error!("the extra feature is required");
"""


def assert_gate(result: ActionResult, failure: str | None) -> None:
    """Assert a gate passed, or failed with the message proving why it failed."""
    output = result.stdout + result.stderr
    if failure is None:
        assert result.code == 0, output
    else:
        assert result.code != 0, output
        assert failure in output, output
