from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import os
import re
import subprocess
import tempfile

import yaml


@dataclass
class ActionResult:
    code: int
    stdout: str
    stderr: str
    outputs: Dict[str, str]


def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists():
            return parent
    return start.resolve()


def _input_env_key(name: str) -> str:
    return "INPUT_" + re.sub(r"[^A-Za-z0-9]", "_", name).upper()


def _resolve_input_ref(text: str, inputs: Dict[str, str]) -> str:
    if not isinstance(text, str):
        return text

    def repl(match: re.Match[str]) -> str:
        raw = match.group(1)
        key = raw.strip()
        key = key.replace("inputs.", "")
        key = key.strip("[]'\"")
        return inputs.get(key, "")

    return re.sub(r"\$\{\{\s*([^}]+)\s*\}\}", repl, text)


def _strip_quotes(value: str) -> str:
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        return value[1:-1]
    return value


def _resolve_condition_value(token: str, inputs: Dict[str, str], step_outputs: Dict[str, Dict[str, str]]) -> str:
    if token.startswith("inputs."):
        return inputs.get(token.split("inputs.", 1)[1], "")
    if token.startswith("steps."):
        _, step_id, _, output_name = token.split(".", 3)
        return step_outputs.get(step_id, {}).get(output_name, "")
    return _strip_quotes(token)


def _eval_condition(expr: str, inputs: Dict[str, str], step_outputs: Dict[str, Dict[str, str]]) -> bool:
    if not expr:
        return True
    parts = [p.strip() for p in expr.split("&&")]
    for part in parts:
        if "==" in part:
            left, right = [p.strip() for p in part.split("==", 1)]
            left_val = _resolve_condition_value(left, inputs, step_outputs)
            right_val = _strip_quotes(right)
            if left_val != right_val:
                return False
        elif "!=" in part:
            left, right = [p.strip() for p in part.split("!=", 1)]
            left_val = _resolve_condition_value(left, inputs, step_outputs)
            right_val = _strip_quotes(right)
            if left_val == right_val:
                return False
        else:
            if not _resolve_condition_value(part, inputs, step_outputs):
                return False
    return True


def run_action(
    action_path: str | Path,
    inputs: Optional[Dict[str, str]] = None,
    env: Optional[Dict[str, str]] = None,
    workdir: Optional[Path] = None,
) -> ActionResult:
    action_path = Path(action_path)
    if action_path.is_dir():
        action_path = action_path / "action.yml"
    data = yaml.safe_load(action_path.read_text())

    repo_root = _find_repo_root(action_path)
    inputs = inputs or {}
    env = env or {}

    action_inputs: Dict[str, str] = {}
    for name, meta in (data.get("inputs") or {}).items():
        if name in inputs:
            action_inputs[name] = str(inputs[name])
        else:
            default = meta.get("default")
            if default is not None:
                action_inputs[name] = str(default)
            elif meta.get("required"):
                raise ValueError(f"Missing required input: {name}")
            else:
                action_inputs[name] = ""

    run_env = {
        "GITHUB_OUTPUT": "",
        "GITHUB_ENV": "",
        "GITHUB_WORKSPACE": str(repo_root),
    }
    for name, value in action_inputs.items():
        run_env[_input_env_key(name)] = value

    step_outputs: Dict[str, Dict[str, str]] = {}
    stdout_all: list[str] = []
    stderr_all: list[str] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(workdir) if workdir else Path(tmpdir)
        workspace.mkdir(parents=True, exist_ok=True)
        gh_output = Path(tmpdir) / "github_output"
        gh_env = Path(tmpdir) / "github_env"
        gh_output.write_text("")
        gh_env.write_text("")

        run_env["GITHUB_OUTPUT"] = str(gh_output)
        run_env["GITHUB_ENV"] = str(gh_env)

        merged_env = os.environ.copy()
        merged_env.update(run_env)
        merged_env.update(env)

        for step in data.get("runs", {}).get("steps", []):
            if "uses" in step:
                continue
            condition = step.get("if")
            if condition and not _eval_condition(condition, action_inputs, step_outputs):
                continue

            step_env = {}
            for key, value in (step.get("env") or {}).items():
                step_env[key] = _resolve_input_ref(value, action_inputs)
            merged_step_env = merged_env.copy()
            merged_step_env.update(step_env)

            run_cmd = step.get("run")
            if not run_cmd:
                continue
            run_cmd = str(run_cmd)

            if run_cmd.startswith("bash scripts/"):
                run_cmd = run_cmd.replace("bash scripts/", f"bash {repo_root / 'scripts'}/", 1)
            elif run_cmd.startswith("scripts/"):
                run_cmd = run_cmd.replace("scripts/", f"{repo_root / 'scripts'}/", 1)

            step_cwd = workspace
            working_dir = step.get("working-directory")
            if working_dir:
                step_cwd = repo_root / str(working_dir)

            proc = subprocess.run(
                ["bash", "-lc", run_cmd],
                cwd=step_cwd,
                env=merged_step_env,
                capture_output=True,
                text=True,
            )
            stdout_all.append(proc.stdout)
            stderr_all.append(proc.stderr)

            step_output_map: Dict[str, str] = {}
            if gh_output.exists():
                for line in gh_output.read_text().splitlines():
                    if not line.strip() or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    step_output_map[key] = value
            step_id = step.get("id")
            if step_id:
                step_outputs[step_id] = step_output_map

            if proc.returncode != 0:
                return ActionResult(
                    code=proc.returncode,
                    stdout="".join(stdout_all),
                    stderr="".join(stderr_all),
                    outputs=step_output_map,
                )

        outputs: Dict[str, str] = {}
        if gh_output.exists():
            for line in gh_output.read_text().splitlines():
                if not line.strip() or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                outputs[key] = value

        return ActionResult(
            code=0,
            stdout="".join(stdout_all),
            stderr="".join(stderr_all),
            outputs=outputs,
        )
