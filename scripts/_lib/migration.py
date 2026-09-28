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


def _single_version(
    plan: MigrationPlan, job: Workflow, setup: Workflow, setting: str, name: str
) -> str | None:
    """Pick one version for a reusable workflow that tests a single version."""
    versions = _values((setup.get("with") or {}).get(setting), job, plan.notes, setting)
    if not versions:
        plan.notes.append(f"No {setting} found; {plan.workflow} uses its default.")
        return None
    newest = _newest(versions)
    if len(versions) > 1:
        plan.notes.append(
            f"{plan.workflow} tests one {name} version; {newest} is the newest of "
            + ", ".join(versions)
            + "."
        )
    return newest


def _not_carried_over(job: Workflow, plan: MigrationPlan, handled: set[str], *setup: str) -> None:
    left = []
    for step in _steps(job):
        if "run" in step:
            if str(step["run"]).strip() in handled:
                continue
            left.append(step.get("name") or str(step["run"]).strip().splitlines()[0])
        elif _action(step) not in (*SETUP_STEPS, *setup):
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
            "This tool migrates Yarn only so far, although node-ci.yml also installs with npm "
            f"and pnpm. This starter uses {manager}, so nothing was generated."
        )
        return plan

    plan = MigrationPlan("node", job_name, "node-ci.yml", {"contents": "read"})
    version = _single_version(plan, job, setup, "node-version", "Node.js")
    if version:
        plan.inputs["node-version"] = version
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


def _plan_bun(job_name: str, job: Workflow, setup: Workflow) -> MigrationPlan:
    plan = MigrationPlan("node", job_name)
    plan.notes.append(
        "node-ci.yml installs with npm, Yarn or pnpm, and this starter uses Bun, so no reusable "
        "workflow of this collection fits it yet and nothing was generated."
    )
    return plan


def _commands_starting(job: Workflow, *tools: str) -> set[str]:
    return {
        command for command in _commands(job) if command.split()[:1] and command.split()[0] in tools
    }


def _plan_go(job_name: str, job: Workflow, setup: Workflow) -> MigrationPlan:
    plan = MigrationPlan("go", job_name, "go-ci.yml", {"contents": "read"})
    version = _single_version(plan, job, setup, "go-version", "Go")
    if version:
        plan.inputs["go-version"] = version
    plan.notes.append(
        "go-ci.yml runs `go test ./...` and golangci-lint on ubuntu-latest; "
        "`go test` compiles every package that has tests."
    )
    handled = {command for command in _commands(job) if command.startswith("go test")}
    _not_carried_over(job, plan, handled, "actions/setup-go")
    return plan


def _java_build_tool(job: Workflow, setup: Workflow) -> str | None:
    cache = str((setup.get("with") or {}).get("cache", "")).strip().lower()
    if cache in {"maven", "gradle"}:
        return cache
    actions = {_action(step) for step in _steps(job)}
    if "gradle/actions/setup-gradle" in actions:
        return "gradle"
    for command in _commands(job):
        tool = command.split()[0] if command.split() else ""
        if tool in {"mvn", "./mvnw"}:
            return "maven"
        if tool in {"gradle", "./gradlew"}:
            return "gradle"
    return None


def _plan_java(job_name: str, job: Workflow, setup: Workflow) -> MigrationPlan:
    plan = MigrationPlan("java", job_name, "java-ci.yml", {"contents": "read"})
    tool = _java_build_tool(job, setup)
    if tool:
        plan.inputs["build-tool"] = tool
    else:
        plan.notes.append(
            "Could not tell Maven from Gradle; java-ci.yml defaults to Maven. Set `build-tool` "
            "to `gradle` for a Gradle project."
        )
    versions = _values(
        (setup.get("with") or {}).get("java-version"), job, plan.notes, "java-version"
    )
    if versions and versions != ["17"]:
        plan.notes.append(
            "java-ci.yml always builds with Temurin JDK 17; the starter asked for "
            + ", ".join(versions)
            + "."
        )
    command = "`./gradlew test`" if tool == "gradle" else "`mvn -B test`"
    plan.notes.append(f"java-ci.yml runs {command}, not the starter's package or build goal.")
    handled = _commands_starting(job, "mvn", "./mvnw", "gradle", "./gradlew")
    _not_carried_over(job, plan, handled, "actions/setup-java", "gradle/actions/setup-gradle")
    return plan


def _plan_ruby(job_name: str, job: Workflow, setup: Workflow) -> MigrationPlan:
    plan = MigrationPlan("ruby", job_name, "ruby-ci.yml", {"contents": "read"})
    versions = _values(
        (setup.get("with") or {}).get("ruby-version"), job, plan.notes, "ruby-version"
    )
    if versions:
        plan.inputs["ruby-versions"] = json.dumps(versions)
    else:
        plan.notes.append("No ruby-version found; ruby-ci.yml tests its default versions.")
    handled: set[str] = set()
    tests = [
        command
        for command in _commands(job)
        if command.startswith(("bundle exec", "rake", "rspec")) and "\n" not in command
    ]
    if len(tests) == 1:
        plan.inputs["test-command"] = tests[0]
        handled.add(tests[0])
    elif tests:
        plan.notes.append("Several test commands found; ruby-ci.yml runs its default command.")
    handled |= {command for command in _commands(job) if command.startswith("bundle install")}
    plan.notes.append("ruby-ci.yml requires a Gemfile and runs on ubuntu-latest.")
    _not_carried_over(job, plan, handled, "ruby/setup-ruby")
    return plan


def _plan_dotnet(job_name: str, job: Workflow, setup: Workflow) -> MigrationPlan:
    plan = MigrationPlan("dotnet", job_name, "dotnet-ci.yml", {"contents": "read"})
    values = _values(
        (setup.get("with") or {}).get("dotnet-version"), job, plan.notes, "dotnet-version"
    )
    # setup-dotnet installs several SDKs when they are listed one per line.
    versions = [version for value in values for version in value.split()]
    if versions:
        plan.inputs["dotnet-version"] = _newest(versions)
        # dotnet-ci.yml runs `dotnet test -f <framework>` for each framework, net8.0 by default.
        frameworks = []
        for version in versions:
            match = re.match(r"(\d+)\.(\d+)", version)
            if match and f"net{match.group(1)}.{match.group(2)}" not in frameworks:
                frameworks.append(f"net{match.group(1)}.{match.group(2)}")
        if frameworks:
            plan.inputs["frameworks"] = json.dumps(frameworks)
            plan.notes.append(
                "frameworks is derived from the SDK versions; set it to the project's target "
                "frameworks if they differ."
            )
    else:
        plan.notes.append("No dotnet-version found; dotnet-ci.yml uses its default.")
    handled = _commands_starting(job, "dotnet")
    _not_carried_over(job, plan, handled, "actions/setup-dotnet")
    return plan


def _plan_deno(job_name: str, job: Workflow, setup: Workflow) -> MigrationPlan:
    plan = MigrationPlan("deno", job_name, "deno-ci.yml", {"contents": "read"})
    version = _single_version(plan, job, setup, "deno-version", "Deno")
    if version:
        plan.inputs["deno-version"] = version
    _os_matrix(job, plan)
    handled = _commands_starting(job, "deno")
    flagged = [
        command
        for command in handled
        if command.split()[:2] == ["deno", "test"] and len(command.split()) > 2
    ]
    if flagged:
        plan.notes.append(
            "deno-ci.yml runs plain `deno lint` and `deno test`; the starter's "
            + ", ".join(f"`{command}`" for command in sorted(flagged))
            + " passes flags, such as permissions, that it does not."
        )
    _not_carried_over(job, plan, handled, "denoland/setup-deno")
    return plan


def _rust_toolchain(setup: Workflow) -> str | None:
    toolchain = (setup.get("with") or {}).get("toolchain")
    if toolchain:
        return str(toolchain)
    ref = str(setup.get("uses", "")).partition("@")[2]
    if (
        _action(setup) == "dtolnay/rust-toolchain"
        and ref
        and not re.fullmatch(r"[0-9a-f]{40}", ref)
    ):
        return ref  # dtolnay/rust-toolchain names the toolchain in its ref, such as @stable.
    return None


def _plan_rust(job_name: str, job: Workflow, setup: Workflow) -> MigrationPlan:
    plan = MigrationPlan("rust", job_name, "rust-ci.yml", {"contents": "read"})
    toolchain = _rust_toolchain(setup) if setup else None
    if toolchain:
        plan.inputs["rust-toolchain"] = toolchain
    plan.notes.append(
        "rust-ci.yml also checks formatting with `cargo fmt --check` and runs Clippy; set "
        "`run-format` or `run-clippy` to false to skip them."
    )
    handled = _commands_starting(job, "cargo")
    _not_carried_over(
        job, plan, handled, "dtolnay/rust-toolchain", "actions-rs/toolchain", "Swatinem/rust-cache"
    )
    return plan


def _plan_r(job_name: str, job: Workflow, setup: Workflow) -> MigrationPlan:
    plan = MigrationPlan("r", job_name)
    plan.notes.append(
        "No public reusable workflow of this collection runs R CMD check yet (the R composite "
        "actions setup-r, r-lint and r-testthat can be used as steps), so nothing was generated."
    )
    return plan


PLANNERS: dict[str, tuple[str, Callable[[str, Workflow, Workflow], MigrationPlan]]] = {
    "actions/setup-python": ("python", _plan_python),
    "actions/setup-node": ("node", _plan_node),
    "oven-sh/setup-bun": ("node", _plan_bun),
    "actions/setup-go": ("go", _plan_go),
    "actions/setup-java": ("java", _plan_java),
    "ruby/setup-ruby": ("ruby", _plan_ruby),
    "actions/setup-dotnet": ("dotnet", _plan_dotnet),
    "denoland/setup-deno": ("deno", _plan_deno),
    "dtolnay/rust-toolchain": ("rust", _plan_rust),
    "actions-rs/toolchain": ("rust", _plan_rust),
    "r-lib/actions/setup-r": ("r", _plan_r),
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
    found = []
    for job_name, job in (workflow.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        setups = [
            (job_name, job, step, PLANNERS[_action(step)])
            for step in _steps(job)
            if _action(step) in PLANNERS
        ]
        # GitHub's Rust starter sets nothing up: runners already have cargo.
        if not setups and _commands_starting(job, "cargo"):
            setups = [(job_name, job, {}, ("rust", _plan_rust))]
        found.extend(setups)
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
