"""Plan, explain and render migrations from GitHub starter workflows.

A starter workflow is read into a :class:`MigrationPlan`: the ecosystem it sets up,
the reusable workflow of this collection that replaces it, the inputs that keep
its settings, and notes on everything that does not carry over. The plan is then
rendered as a workflow, explained as text, or reported as JSON.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import json
import re
from typing import Any, Callable

import yaml

from scripts._lib.workflows import CONSUMER_REF, REPO

MATRIX_REFERENCE = re.compile(r"\$\{\{\s*matrix\.([\w-]+)\s*\}\}")
# GitHub replaces this placeholder when a starter is added through its UI; a copy of
# the raw template still contains it.
DEFAULT_BRANCH_PLACEHOLDER = "$default-branch"
SETUP_STEPS = ("actions/checkout",)
PYTHON_TEST_COMMANDS = ("pytest", "python -m pytest")
PYTHON_LINTERS = ("flake8", "ruff", "pylint", "mypy", "black")

Workflow = dict[Any, Any]


@dataclass
class MigrationPlan:
    """What a starter workflow becomes, and why."""

    ecosystem: str
    job: str
    workflow: str | None = None
    permissions: dict[str, str] = field(default_factory=dict)
    inputs: dict[str, str] = field(default_factory=dict)
    name: str = ""
    triggers: Any = None
    notes: list[str] = field(default_factory=list)

    @property
    def uses(self) -> str | None:
        if self.workflow is None:
            return None
        return f"{REPO}/.github/workflows/{self.workflow}@{CONSUMER_REF}"


def _steps(job: Workflow) -> list[Workflow]:
    return [step for step in job.get("steps") or [] if isinstance(step, dict)]


def _action(step: Workflow) -> str:
    return str(step.get("uses", "")).split("@", 1)[0]


def _commands(job: Workflow) -> list[str]:
    return [str(step["run"]).strip() for step in _steps(job) if "run" in step]


def _values(value: Any, job: Workflow, notes: list[str], setting: str) -> list[str]:
    """Return the concrete values of a starter setting, following `${{ matrix.<key> }}`."""
    if value is None or str(value).strip() == "":
        return []
    match = MATRIX_REFERENCE.fullmatch(str(value).strip())
    if match is None:
        entries: list[Any] = [value]
    else:
        matrix = (job.get("strategy") or {}).get("matrix") or {}
        listed = matrix.get(match.group(1)) if isinstance(matrix, dict) else None
        if not isinstance(listed, list) or not listed:
            notes.append(
                f"Could not resolve {value} for {setting}; the reusable workflow's default is used."
            )
            return []
        entries = listed
    if any(isinstance(entry, float) for entry in entries):
        notes.append(
            f"YAML read a {setting} value as a number, so a version such as 3.10 became 3.1. "
            "Quote the versions in the starter and migrate it again."
        )
    return [str(entry) for entry in entries]


def _newest(versions: list[str]) -> str:
    return max(versions, key=lambda version: [int(part) for part in re.findall(r"\d+", version)])


def _os_matrix(job: Workflow, plan: MigrationPlan) -> None:
    runs_on = job.get("runs-on")
    if not isinstance(runs_on, str):
        if runs_on is not None:
            plan.notes.append(
                "runs-on is not a single label, so the default operating systems are used."
            )
        return
    systems = _values(runs_on, job, plan.notes, "runs-on")
    if systems:
        plan.inputs["os-matrix"] = json.dumps(systems)


def _not_carried_over(job: Workflow, plan: MigrationPlan, handled: set[str], setup: str) -> None:
    left = []
    for step in _steps(job):
        if "run" in step:
            if str(step["run"]).strip() in handled:
                continue
            left.append(step.get("name") or str(step["run"]).strip().splitlines()[0])
        elif _action(step) not in (*SETUP_STEPS, setup):
            left.append(step.get("name") or _action(step))
    if left:
        plan.notes.append(
            "Not carried over; check that the reusable workflow covers them: "
            + ", ".join(f"`{name}`" for name in left)
            + "."
        )


def _plan_python(job_name: str, job: Workflow, setup: Workflow) -> MigrationPlan:
    plan = MigrationPlan("python", job_name, "python-test-matrix.yml", {"contents": "read"})
    settings = setup.get("with") or {}
    versions = _values(settings.get("python-version"), job, plan.notes, "python-version")
    if versions:
        plan.inputs["python-versions"] = json.dumps(versions)
    else:
        plan.notes.append(
            "No Python version found; python-test-matrix.yml tests its default versions."
        )
    _os_matrix(job, plan)

    handled: set[str] = set()
    tests = [command for command in _commands(job) if command.startswith(PYTHON_TEST_COMMANDS)]
    if len(tests) == 1 and "\n" not in tests[0]:
        plan.inputs["test-command"] = tests[0]
        handled.add(tests[0])
    elif tests:
        plan.notes.append(
            "Several test commands found; python-test-matrix.yml runs its default `pytest -q`."
        )
    plan.notes.append(
        "python-test-matrix.yml installs the project itself (`pip install .`, or "
        "`requirements.txt` without a pyproject.toml) together with pytest."
    )
    if any(linter in command for command in _commands(job) for linter in PYTHON_LINTERS):
        plan.notes.append("The starter also lints; add python-lint.yml for that.")
    _not_carried_over(job, plan, handled, "actions/setup-python")
    return plan


def _package_manager(job: Workflow, setup: Workflow) -> str:
    cache = str((setup.get("with") or {}).get("cache", "")).strip().lower()
    if cache in {"npm", "yarn", "pnpm"}:
        return cache
    if any(_action(step) == "pnpm/action-setup" for step in _steps(job)):
        return "pnpm"
    for command in _commands(job):
        tool = command.split()[0] if command.split() else ""
        if tool in {"npm", "yarn", "pnpm"}:
            return tool
    return "npm"


def _plan_node(job_name: str, job: Workflow, setup: Workflow) -> MigrationPlan:
    manager = _package_manager(job, setup)
    if manager != "yarn":
        plan = MigrationPlan("node", job_name)
        plan.notes.append(
            "node-ci.yml supports Yarn only: it runs `yarn install --immutable`, `yarn lint` "
            f"and `yarn test`. This starter uses {manager}, so no reusable workflow of this "
            "collection fits it yet and nothing was generated."
        )
        return plan

    plan = MigrationPlan("node", job_name, "node-ci.yml", {"contents": "read"})
    versions = _values(
        (setup.get("with") or {}).get("node-version"), job, plan.notes, "node-version"
    )
    if versions:
        newest = _newest(versions)
        plan.inputs["node-version"] = newest
        if len(versions) > 1:
            plan.notes.append(
                f"node-ci.yml tests one Node.js version; {newest} is the newest of "
                + ", ".join(versions)
                + "."
            )
    else:
        plan.notes.append("No Node.js version found; node-ci.yml uses its default.")
    _os_matrix(job, plan)
    plan.notes.append("node-ci.yml also runs `yarn lint`, so package.json needs a lint script.")
    # node-ci.yml installs, lints and tests; any other Yarn script, such as a build, is not run.
    handled = {
        command
        for command in _commands(job)
        if command.split()[:1] == ["yarn"]
        and command.split()[1:2] in ([], ["install"], ["lint"], ["test"])
    }
    _not_carried_over(job, plan, handled, "actions/setup-node")
    return plan


PLANNERS: dict[str, tuple[str, Callable[[str, Workflow, Workflow], MigrationPlan]]] = {
    "actions/setup-python": ("python", _plan_python),
    "actions/setup-node": ("node", _plan_node),
}


def _triggers(workflow: Workflow, default_branch: str, notes: list[str]) -> Any:
    triggers = copy.deepcopy(workflow.get("on") or workflow.get(True) or {})
    replaced = False

    def replace(node: Any) -> Any:
        nonlocal replaced
        if isinstance(node, dict):
            return {key: replace(value) for key, value in node.items()}
        if isinstance(node, list):
            return [replace(value) for value in node]
        if node == DEFAULT_BRANCH_PLACEHOLDER:
            replaced = True
            return default_branch
        return node

    triggers = replace(triggers)
    if replaced:
        notes.append(
            f"Replaced the `{DEFAULT_BRANCH_PLACEHOLDER}` placeholder with `{default_branch}`."
        )
    return triggers


def plan_migration(workflow: Workflow, default_branch: str = "main") -> MigrationPlan:
    """Plan how the first job that sets up a known ecosystem migrates."""
    found = [
        (name, job, step, PLANNERS[_action(step)])
        for name, job in (workflow.get("jobs") or {}).items()
        if isinstance(job, dict)
        for step in _steps(job)
        if _action(step) in PLANNERS
    ]
    if not found:
        raise SystemExit("Unable to detect language from starter workflow")

    name, job, step, (_, planner) = found[0]
    plan = planner(name, job, step)
    others = sorted(
        {
            f"{ecosystem} in job `{other}`"
            for other, _, _, (ecosystem, _) in found[1:]
            if other != name
        }
    )
    if others:
        plan.notes.append("Also found " + ", ".join(others) + "; migrate it separately.")
    plan.triggers = _triggers(workflow, default_branch, plan.notes)
    plan.name = str(workflow.get("name") or f"{plan.ecosystem.title()} CI")
    return plan


def render_migration(plan: MigrationPlan) -> str:
    """Render the workflow that calls the reusable workflow of *plan*."""
    if plan.uses is None:
        raise ValueError("this plan has no reusable workflow to call")
    job: dict[str, Any] = {"permissions": dict(plan.permissions), "uses": plan.uses}
    if plan.inputs:
        job["with"] = dict(plan.inputs)
    document = {
        "name": plan.name or f"{plan.ecosystem.title()} CI",
        "on": plan.triggers or {},
        "jobs": {"ci": job},
    }
    return yaml.safe_dump(document, sort_keys=False)


def explain(plan: MigrationPlan) -> str:
    """Describe the plan for a person deciding whether to apply it."""
    lines = [f"Detected: {plan.ecosystem} (job `{plan.job}`)"]
    if plan.uses:
        lines.append(f"Calls: {plan.uses}")
        for key, value in plan.inputs.items():
            lines.append(f"  with {key}: {value}")
    else:
        lines.append("Calls: nothing; no reusable workflow fits this starter yet")
    lines.extend(f"- {note}" for note in plan.notes)
    return "\n".join(lines) + "\n"


def migration_report(
    plan: MigrationPlan, *, source: str, output: str | None, migrated: str | None
) -> dict[str, Any]:
    """Describe the plan for tools; `migrated` is the rendered workflow, if any."""
    return {
        "source": source,
        "ecosystem": plan.ecosystem,
        "job": plan.job,
        "workflow": plan.workflow,
        "uses": plan.uses,
        "permissions": plan.permissions,
        "inputs": plan.inputs,
        "notes": plan.notes,
        "output": output,
        "migrated": migrated,
    }


def load_workflow(content: str) -> Workflow:
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise SystemExit(f"Invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Starter workflow must be a YAML mapping")
    return data


def convert(content: str, default_branch: str = "main") -> str:
    """Return the migrated workflow, or exit with the reason there is none."""
    plan = plan_migration(load_workflow(content), default_branch)
    if plan.uses is None:
        raise SystemExit(explain(plan))
    return render_migration(plan)
