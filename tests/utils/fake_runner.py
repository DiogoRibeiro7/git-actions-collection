"""Small deterministic runner for shell-backed composite-action tests.

The runner intentionally implements only the GitHub expression contexts needed
by this repository. It is not a replacement for the GitHub Actions runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    step_outputs: dict[str, dict[str, str]] = field(default_factory=dict)
    skipped_uses: tuple[str, ...] = ()
    executed_steps: int = 0
    summary: str = ""


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
        return inputs[key.removeprefix("inputs.")]
    output_reference = re.fullmatch(r"steps\.([\w-]+)\.outputs\.([\w-]+)", key)
    if output_reference:
        return step_outputs.get(output_reference[1], {}).get(output_reference[2], "")
    if key.startswith("github."):
        return github[key.removeprefix("github.")]
    raise ValueError(f"Unsupported action expression: {expression}")


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
        return inputs[token.split("inputs.", 1)[1]]
    if token.startswith("steps."):
        parts = token.split(".")
        if len(parts) == 4 and parts[2] == "outputs":
            return step_outputs.get(parts[1], {}).get(parts[3], "")
    return _strip_quotes(token)


def _eval_condition(
    expression: str | bool,
    inputs: Mapping[str, str],
    step_outputs: Mapping[str, Mapping[str, str]],
) -> bool:
    """Evaluate the simple boolean conditions used in local action fixtures."""
    if isinstance(expression, bool):
        return expression
    if not expression:
        return True
    expression = expression.strip()
    if expression.startswith("${{") and expression.endswith("}}"):
        expression = expression[3:-2].strip()
    # This harness supports comparisons joined by &&, not the full expression
    # language. Reject anything else instead of treating it as a truthy string.
    comparisons: list[tuple[str, str, str]] = []
    for part in (item.strip() for item in expression.split("&&")):
        match = re.fullmatch(
            r"(inputs\.[\w-]+|steps\.[\w-]+\.outputs\.[\w-]+)\s*(==|!=)\s*'([^']*)'",
            part,
        )
        if match is None:
            raise ValueError(f"Unsupported action condition: {expression}")
        comparisons.append((match[1], match[2], match[3]))
    for left, operator, right in comparisons:
        equal = _resolve_condition_value(left, inputs, step_outputs) == right
        if equal != (operator == "=="):
            return False
    return True


def _read_outputs(path: Path) -> dict[str, str]:
    """Read single-line and heredoc entries from a GitHub command file."""
    outputs: dict[str, str] = {}
    if not path.exists():
        return outputs
    lines = iter(path.read_text(encoding="utf-8").splitlines())
    for line in lines:
        if not line:
            continue
        if "<<" in line and ("=" not in line or line.index("<<") < line.index("=")):
            key, delimiter = line.split("<<", 1)
            value_lines = []
            for item in lines:
                if item == delimiter:
                    break
                value_lines.append(item)
            else:
                raise ValueError(f"Unterminated command-file value: {key}")
            outputs[key] = "\n".join(value_lines)
        elif "=" in line:
            key, value = line.split("=", 1)
            outputs[key] = value
        else:
            raise ValueError(f"Invalid command-file entry: {line}")
    return outputs


def run_action(
    action_path: str | Path,
    inputs: Mapping[str, str] | None = None,
    env: Mapping[str, str] | None = None,
    workdir: Path | None = None,
) -> ActionResult:
    """Execute Bash steps, reporting skipped dependencies and public outputs.

    External ``uses:`` steps are not executed. Callers must stub their effects;
    an action containing only dependencies requires a contract/integration test.
    """
    action_file = Path(action_path)
    if action_file.is_dir():
        action_file = action_file / "action.yml"
    data = yaml.safe_load(action_file.read_text(encoding="utf-8"))

    if data.get("runs", {}).get("using") != "composite":
        raise ValueError("The fake runner only supports composite actions")
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
    skipped_uses: list[str] = []
    executed_steps = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(workdir) if workdir else Path(tmpdir) / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)

        github_context = {
            "workspace": str(workspace),
            "action_path": str(action_file.parent.resolve()),
            "sha": supplied_env.get("GITHUB_SHA", "test-sha"),
            "event.pull_request.body": supplied_env.get("PR_BODY", ""),
        }

        run_env = os.environ.copy()
        run_env.update(
            {
                "GITHUB_WORKSPACE": str(workspace),
                "GITHUB_ACTION_PATH": str(action_file.parent.resolve()),
            }
        )
        run_env.update(supplied_env)

        for index, step in enumerate(data.get("runs", {}).get("steps", [])):
            condition = step.get("if", "")
            if not _eval_condition(condition, action_inputs, step_outputs):
                continue
            if "uses" in step:
                skipped_uses.append(step["uses"])
                continue
            if step.get("shell") != "bash":
                raise ValueError(f"Unsupported action shell: {step.get('shell')}")

            gh_output = Path(tmpdir) / f"output-{index}"
            gh_env = Path(tmpdir) / f"env-{index}"
            gh_output.touch()
            gh_env.touch()
            run_env["GITHUB_OUTPUT"] = supplied_env.get("GITHUB_OUTPUT", str(gh_output))
            run_env["GITHUB_ENV"] = supplied_env.get("GITHUB_ENV", str(gh_env))

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

            executed_steps += 1
            proc = subprocess.run(
                ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", run_cmd],
                cwd=step_cwd,
                env=merged_step_env,
                capture_output=True,
                text=True,
                check=False,
            )
            stdout_all.append(proc.stdout)
            stderr_all.append(proc.stderr)

            output_path = merged_step_env.get("GITHUB_OUTPUT")
            current_outputs = _read_outputs(Path(output_path)) if output_path else {}
            if step.get("id"):
                step_outputs[str(step["id"])] = current_outputs.copy()
            env_path = merged_step_env.get("GITHUB_ENV")
            if env_path:
                run_env.update(_read_outputs(Path(env_path)))

            if proc.returncode != 0:
                return ActionResult(
                    code=proc.returncode,
                    stdout="".join(stdout_all),
                    stderr="".join(stderr_all),
                    outputs={},
                    step_outputs=step_outputs,
                    skipped_uses=tuple(skipped_uses),
                    executed_steps=executed_steps,
                )

        if not any("run" in step for step in data["runs"]["steps"]):
            raise ValueError("No shell steps executed; use a contract or GitHub integration test")
        return ActionResult(
            code=0,
            stdout="".join(stdout_all),
            stderr="".join(stderr_all),
            outputs={
                name: _resolve_expressions(
                    metadata["value"], inputs=action_inputs,
                    step_outputs=step_outputs, github=github_context,
                )
                for name, metadata in (data.get("outputs") or {}).items()
            },
            step_outputs=step_outputs,
            skipped_uses=tuple(skipped_uses),
            executed_steps=executed_steps,
        )


def run_workflow_step(
    workflow_path: str | Path,
    job: str,
    step_name: str,
    context: Mapping[str, str],
    env: Mapping[str, str] | None = None,
    workdir: Path | None = None,
) -> ActionResult:
    """Execute one named shell step from a reusable-workflow job.

    Every ``${{ ... }}`` expression in the step must be supplied through
    *context*, keyed by its expression text (for example ``github.sha``), so a
    test can never silently run the step with empty values.
    """
    data = yaml.safe_load(Path(workflow_path).read_text(encoding="utf-8"))
    step = next(
        item for item in data["jobs"][job]["steps"] if item.get("name") == step_name
    )

    def resolve(value: object) -> str:
        def replacement(match: re.Match[str]) -> str:
            expression = match.group(1)
            if expression not in context:
                raise KeyError(f"unresolved expression in {step_name!r}: {expression}")
            return context[expression]

        return re.sub(r"\$\{\{\s*([^}]+?)\s*\}\}", replacement, str(value))

    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = Path(workdir) if workdir else Path(tmpdir)
        if step.get("working-directory") is not None:
            cwd = cwd / resolve(step["working-directory"])
        gh_output = Path(tmpdir) / "github_output"
        gh_summary = Path(tmpdir) / "github_step_summary"
        gh_output.write_text("", encoding="utf-8")
        gh_summary.write_text("", encoding="utf-8")

        run_env = os.environ.copy()
        run_env.update(
            {
                "GITHUB_OUTPUT": str(gh_output),
                "GITHUB_STEP_SUMMARY": str(gh_summary),
                "RUNNER_TEMP": tmpdir,
            }
        )
        run_env.update(env or {})
        run_env.update({key: resolve(value) for key, value in (step.get("env") or {}).items()})

        proc = subprocess.run(
            ["bash", "-c", resolve(step["run"])],
            cwd=cwd,
            env=run_env,
            capture_output=True,
            text=True,
            check=False,
        )
        return ActionResult(
            code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            outputs=_read_outputs(gh_output),
            summary=Path(run_env["GITHUB_STEP_SUMMARY"]).read_text(encoding="utf-8"),
        )
