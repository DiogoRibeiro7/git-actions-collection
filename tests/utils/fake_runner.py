"""Small deterministic runner for shell-backed composite-action tests.

The runner intentionally implements only the GitHub expression contexts needed
by this repository. It is not a replacement for the GitHub Actions runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Mapping

import yaml


@dataclass(frozen=True)
class ActionResult:
    """Result returned by a simulated composite action."""

    code: int
    stdout: str
    stderr: str
    outputs: dict[str, str]


def _find_repo_root(start: Path) -> Path:
    """Find the repository root by walking upwards from *start*."""
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    return start.resolve()


def _input_env_key(name: str) -> str:
    """Convert a GitHub Action input name into its conventional env key."""
    return "INPUT_" + re.sub(r"[^A-Za-z0-9]", "_", name).upper()


def _lookup_expression(
    expression: str,
    *,
    inputs: Mapping[str, str],
    step_outputs: Mapping[str, Mapping[str, str]],
    github: Mapping[str, str],
) -> str:
    """Resolve the small subset of GitHub expressions used by the test suite."""
    key = expression.strip()
    if key.startswith("inputs."):
        return inputs.get(key.removeprefix("inputs."), "")
    if key.startswith("steps."):
        parts = key.split(".")
        if len(parts) == 4 and parts[2] == "outputs":
            return step_outputs.get(parts[1], {}).get(parts[3], "")
    if key.startswith("github."):
        return github.get(key.removeprefix("github."), "")
    return ""


def _resolve_expressions(
    value: object,
    *,
    inputs: Mapping[str, str],
    step_outputs: Mapping[str, Mapping[str, str]],
    github: Mapping[str, str],
) -> str:
    """Resolve `${{ ... }}` expressions inside a scalar value."""
    text = str(value)

    def replacement(match: re.Match[str]) -> str:
        return _lookup_expression(
            match.group(1),
            inputs=inputs,
            step_outputs=step_outputs,
            github=github,
        )

    return re.sub(r"\$\{\{\s*([^}]+?)\s*\}\}", replacement, text)


def _strip_quotes(value: str) -> str:
    """Remove one matching pair of simple shell-style quotes."""
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        return value[1:-1]
    return value


def _resolve_condition_value(
    token: str,
    inputs: Mapping[str, str],
    step_outputs: Mapping[str, Mapping[str, str]],
) -> str:
    """Resolve values used by the limited `if` expression evaluator."""
    if token.startswith("inputs."):
        return inputs.get(token.split("inputs.", 1)[1], "")
    if token.startswith("steps."):
        parts = token.split(".")
        if len(parts) == 4 and parts[2] == "outputs":
            return step_outputs.get(parts[1], {}).get(parts[3], "")
    return _strip_quotes(token)


def _eval_condition(
    expression: str,
    inputs: Mapping[str, str],
    step_outputs: Mapping[str, Mapping[str, str]],
) -> bool:
    """Evaluate the simple boolean conditions used in local action fixtures."""
    if not expression:
        return True
    for part in (item.strip() for item in expression.split("&&")):
        if "==" in part:
            left, right = [item.strip() for item in part.split("==", 1)]
            if _resolve_condition_value(left, inputs, step_outputs) != _strip_quotes(right):
                return False
        elif "!=" in part:
            left, right = [item.strip() for item in part.split("!=", 1)]
            if _resolve_condition_value(left, inputs, step_outputs) == _strip_quotes(right):
                return False
        elif not _resolve_condition_value(part, inputs, step_outputs):
            return False
    return True


def _read_outputs(path: Path) -> dict[str, str]:
    """Read simple `key=value` entries from a GitHub output file."""
    outputs: dict[str, str] = {}
    if not path.exists():
        return outputs
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and "=" in line:
            key, value = line.split("=", 1)
            outputs[key] = value
    return outputs


def run_action(
    action_path: str | Path,
    inputs: Mapping[str, str] | None = None,
    env: Mapping[str, str] | None = None,
    workdir: Path | None = None,
) -> ActionResult:
    """Execute the shell steps of a local composite action deterministically."""
    action_file = Path(action_path)
    if action_file.is_dir():
        action_file = action_file / "action.yml"
    data = yaml.safe_load(action_file.read_text(encoding="utf-8"))

    repo_root = _find_repo_root(action_file)
    supplied_inputs = dict(inputs or {})
    supplied_env = dict(env or {})

    action_inputs: dict[str, str] = {}
    for name, meta in (data.get("inputs") or {}).items():
        if name in supplied_inputs:
            action_inputs[name] = str(supplied_inputs[name])
        elif meta.get("default") is not None:
            action_inputs[name] = str(meta["default"])
        elif meta.get("required"):
            raise ValueError(f"Missing required input: {name}")
        else:
            action_inputs[name] = ""

    step_outputs: dict[str, dict[str, str]] = {}
    stdout_all: list[str] = []
    stderr_all: list[str] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(workdir) if workdir else Path(tmpdir) / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        gh_output = Path(tmpdir) / "github_output"
        gh_env = Path(tmpdir) / "github_env"
        gh_output.write_text("", encoding="utf-8")
        gh_env.write_text("", encoding="utf-8")

        github_context = {
            "workspace": str(workspace),
            "action_path": str(action_file.parent.resolve()),
            "sha": supplied_env.get("GITHUB_SHA", "test-sha"),
            "event.pull_request.body": supplied_env.get("PR_BODY", ""),
        }

        run_env = os.environ.copy()
        run_env.update(
            {
                "GITHUB_OUTPUT": str(gh_output),
                "GITHUB_ENV": str(gh_env),
                "GITHUB_WORKSPACE": str(workspace),
                "GITHUB_ACTION_PATH": str(action_file.parent.resolve()),
            }
        )
        for name, value in action_inputs.items():
            run_env[_input_env_key(name)] = value
        run_env.update(supplied_env)

        for step in data.get("runs", {}).get("steps", []):
            if "uses" in step:
                continue
            condition = str(step.get("if") or "")
            if condition and not _eval_condition(condition, action_inputs, step_outputs):
                continue

            step_env: dict[str, str] = {}
            for key, value in (step.get("env") or {}).items():
                step_env[key] = _resolve_expressions(
                    value,
                    inputs=action_inputs,
                    step_outputs=step_outputs,
                    github=github_context,
                )
            merged_step_env = run_env.copy()
            merged_step_env.update(step_env)

            raw_command = step.get("run")
            if not raw_command:
                continue
            run_cmd = _resolve_expressions(
                raw_command,
                inputs=action_inputs,
                step_outputs=step_outputs,
                github=github_context,
            )

            # Existing actions keep helper scripts at repository root. Resolve
            # those paths explicitly so local simulation is independent of cwd.
            if run_cmd.startswith("bash scripts/"):
                run_cmd = run_cmd.replace("bash scripts/", f'bash "{repo_root}/scripts/', 1)
                script_end = run_cmd.find(" ", len(f'bash "{repo_root}/scripts/'))
                if script_end == -1:
                    run_cmd += '"'
                else:
                    run_cmd = run_cmd[:script_end] + '"' + run_cmd[script_end:]
            elif run_cmd.startswith("scripts/"):
                run_cmd = run_cmd.replace("scripts/", f'"{repo_root}/scripts/', 1) + '"'

            step_cwd = workspace
            if step.get("working-directory") is not None:
                resolved_dir = _resolve_expressions(
                    step["working-directory"],
                    inputs=action_inputs,
                    step_outputs=step_outputs,
                    github=github_context,
                )
                candidate = Path(resolved_dir)
                step_cwd = candidate if candidate.is_absolute() else workspace / candidate
                step_cwd.mkdir(parents=True, exist_ok=True)

            proc = subprocess.run(
                ["bash", "-c", run_cmd],
                cwd=step_cwd,
                env=merged_step_env,
                capture_output=True,
                text=True,
                check=False,
            )
            stdout_all.append(proc.stdout)
            stderr_all.append(proc.stderr)

            current_outputs = _read_outputs(gh_output)
            if step.get("id"):
                step_outputs[str(step["id"])] = current_outputs.copy()

            if proc.returncode != 0:
                return ActionResult(
                    code=proc.returncode,
                    stdout="".join(stdout_all),
                    stderr="".join(stderr_all),
                    outputs=current_outputs,
                )

        return ActionResult(
            code=0,
            stdout="".join(stdout_all),
            stderr="".join(stderr_all),
            outputs=_read_outputs(gh_output),
        )
