"""Consumer material must call the collection the way it is defined today.

Examples, documentation snippets and generated workflows are what consumers copy.
Every reference to this collection must name a workflow or action that still
exists, use the current major tag or an exact commit SHA, pass only inputs and
secrets the target declares, supply the required ones, avoid deprecated inputs,
and, when the caller declares permissions, grant everything the target's jobs
request. GitHub checks those grants before any job starts, so a shortfall fails
the whole run without a single job appearing on the pull request.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from pathlib import Path
import re
import subprocess
import tomllib
from typing import Any

import pytest
import yaml

from scripts._lib.workflows import generate_migrated
from scripts.interface_snapshot import LEVELS, action_interface, workflow_interface
from scripts.pypi_trusted_publishing_wizard import WORKFLOW_TEMPLATE

ROOT = Path(__file__).resolve().parents[1]
SLUG = "DiogoRibeiro7/git-actions-collection/"
REFERENCE = re.compile(
    re.escape(SLUG) + r"(\.github/(?:workflows/[\w.-]+\.ya?ml|actions/[\w.-]+))@([\w.-]+)"
)
FENCED_YAML = re.compile(r"^```ya?ml[ \t]*\n(.*?)^```", re.MULTILINE | re.DOTALL)
SHA = re.compile(r"[0-9a-f]{40}")
SUFFIXES = {".md", ".yml", ".yaml", ".code-snippets"}


def _major_tag() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return "v" + str(data["project"]["version"]).split(".")[0]


def consumer_documents() -> list[tuple[str, str]]:
    """Return (label, text) for everything a consumer might copy.

    The changelog records history, and tests use made-up components on purpose.
    """
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.splitlines()
    documents = [
        (relative, (ROOT / relative).read_text(encoding="utf-8"))
        for relative in tracked
        if Path(relative).suffix in SUFFIXES
        and relative != "CHANGELOG.md"
        and not relative.startswith("tests/")
    ]
    documents.append(("pypi_trusted_publishing_wizard.py template", WORKFLOW_TEMPLATE))
    for language, version in (("python", "3.12"), ("node", "24")):
        documents.append(
            (
                f"migrate_starter_workflows.py {language} output",
                generate_migrated({"on": {"push": {}}}, language, version),
            )
        )
    return documents


def _yaml_blocks(label: str, text: str) -> list[Any]:
    if label.endswith(".code-snippets"):
        return []
    blocks = FENCED_YAML.findall(text) if label.endswith(".md") else [text]
    parsed = []
    for block in blocks:
        try:
            parsed.append(yaml.safe_load(block))
        except yaml.YAMLError:
            # Prose snippets with placeholders are covered by the textual check.
            continue
    return parsed


def _target(uses: str) -> str:
    return uses.removeprefix(SLUG).rsplit("@", 1)[0]


def _interface(target: str) -> dict[str, Any] | None:
    """Return the target's interface, or None when it does not exist."""
    if target.startswith(".github/workflows/"):
        path = ROOT / target
        if not path.is_file():
            return None
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        triggers = data.get("on") or data.get(True) or {}
        if not isinstance(triggers, Mapping) or "workflow_call" not in triggers:
            return None
        return workflow_interface(ROOT, path.name)
    name = target.removeprefix(".github/actions/")
    if not (ROOT / target / "action.yml").is_file():
        return None
    return action_interface(ROOT, name)


def _callers(node: Any) -> Iterator[Mapping[str, Any]]:
    """Yield every job or step that uses a component of this collection."""
    if isinstance(node, Mapping):
        uses = node.get("uses")
        if isinstance(uses, str) and uses.startswith(SLUG):
            yield node
        for value in node.values():
            yield from _callers(value)
    elif isinstance(node, list):
        for item in node:
            yield from _callers(item)


def _granted(permissions: Any, scope: str) -> str:
    if isinstance(permissions, str):
        return permissions.removesuffix("-all")
    if isinstance(permissions, Mapping):
        return str(permissions.get(scope, "none"))
    return "none"


def reference_problems(label: str, text: str) -> list[str]:
    """Describe every way the document's references disagree with the collection."""
    problems: list[str] = []
    major = _major_tag()
    for target, ref in REFERENCE.findall(text):
        if _interface(target) is None:
            problems.append(f"{label}: {target} is not a reusable workflow or action here")
        if ref != major and not SHA.fullmatch(ref):
            problems.append(f"{label}: {target}@{ref} must use @{major} or a commit SHA")

    for document in _yaml_blocks(label, text):
        for caller in _callers(document):
            target = _target(caller["uses"])
            interface = _interface(target)
            if interface is None:
                continue
            problems.extend(_input_problems(label, target, caller, interface))
            if target.startswith(".github/workflows/"):
                problems.extend(_secret_problems(label, target, caller, interface))
        problems.extend(_permission_problems(label, document))
    return problems


def _input_problems(
    label: str, target: str, caller: Mapping[str, Any], interface: Mapping[str, Any]
) -> list[str]:
    given = caller.get("with") or {}
    inputs = interface["inputs"]
    problems = [f"{label}: {target} has no input {key!r}" for key in given if key not in inputs]
    problems += [
        f"{label}: {target} input {key!r} is deprecated"
        for key in given
        if key in inputs and inputs[key]["deprecated"]
    ]
    workflow = target.startswith(".github/workflows/")
    problems += [
        f"{label}: {target} needs input {key!r}"
        for key, spec in inputs.items()
        if spec["required"] and (workflow or spec["default"] is None) and key not in given
    ]
    return problems


def _secret_problems(
    label: str, target: str, caller: Mapping[str, Any], interface: Mapping[str, Any]
) -> list[str]:
    given = caller.get("secrets")
    if given == "inherit":
        return []
    given = given if isinstance(given, Mapping) else {}
    secrets = interface["secrets"]
    problems = [f"{label}: {target} has no secret {key!r}" for key in given if key not in secrets]
    problems += [
        f"{label}: {target} needs secret {key!r}"
        for key, spec in secrets.items()
        if spec["required"] and key not in given
    ]
    return problems


def _permission_problems(label: str, document: Any) -> list[str]:
    """Check that callers which declare permissions grant what the target requests."""
    if not isinstance(document, Mapping) or not isinstance(document.get("jobs"), Mapping):
        return []
    problems: list[str] = []
    for name, job in document["jobs"].items():
        if not isinstance(job, Mapping) or not str(job.get("uses", "")).startswith(SLUG):
            continue
        target = _target(job["uses"])
        interface = _interface(target)
        granted = job.get("permissions", document.get("permissions"))
        if interface is None or granted is None:
            continue
        for scope, level in interface.get("permissions", {}).items():
            if scope == "*":
                continue
            if LEVELS[_granted(granted, scope)] < LEVELS[level]:
                problems.append(
                    f"{label}: job {name!r} must grant {scope}: {level} for {target}"
                )
    return problems


DOCUMENTS = consumer_documents()


def test_consumer_material_references_the_collection_as_it_is() -> None:
    problems = [problem for label, text in DOCUMENTS for problem in reference_problems(label, text)]

    assert not problems, "Stale consumer references:\n" + "\n".join(problems)


def test_the_audit_sees_the_examples_and_generated_workflows() -> None:
    labels = {label for label, text in DOCUMENTS if SLUG in text}

    assert "examples/python-package/.github/workflows/security.yml" in labels
    assert "README.md" in labels
    assert "pypi_trusted_publishing_wizard.py template" in labels
    assert "migrate_starter_workflows.py python output" in labels
    assert sum(len(REFERENCE.findall(text)) for _, text in DOCUMENTS) > 50


WORKFLOW = SLUG + ".github/workflows/security-scan.yml@v1"


@pytest.mark.parametrize(
    ("snippet", "problem"),
    [
        (
            f"jobs:\n  a:\n    uses: {SLUG}.github/workflows/retired.yml@v1\n",
            ".github/workflows/retired.yml is not a reusable workflow or action here",
        ),
        (
            f"jobs:\n  a:\n    uses: {SLUG}.github/workflows/security-scan.yml@main\n",
            ".github/workflows/security-scan.yml@main must use @v1 or a commit SHA",
        ),
        (
            f"jobs:\n  a:\n    uses: {WORKFLOW}\n    with:\n      path: .\n",
            ".github/workflows/security-scan.yml has no input 'path'",
        ),
        (
            f"jobs:\n  a:\n    uses: {WORKFLOW}\n    secrets:\n      TOKEN: x\n",
            ".github/workflows/security-scan.yml has no secret 'TOKEN'",
        ),
        (
            f"jobs:\n  a:\n    uses: {SLUG}.github/workflows/helm-chart-lint-test.yml@v1\n"
            "    with:\n      publish: false\n",
            ".github/workflows/helm-chart-lint-test.yml input 'publish' is deprecated",
        ),
        (
            f"permissions:\n  contents: read\n  security-events: write\n"
            f"jobs:\n  scan:\n    uses: {WORKFLOW}\n",
            "job 'scan' must grant id-token: write for .github/workflows/security-scan.yml",
        ),
        (
            f"steps:\n  - uses: {SLUG}.github/actions/setup-r@v1\n    with:\n      r: '4'\n",
            ".github/actions/setup-r has no input 'r'",
        ),
    ],
)
def test_the_audit_reports_stale_references(snippet: str, problem: str) -> None:
    assert f"snippet.yml: {problem}" in reference_problems("snippet.yml", snippet)


def test_a_job_level_grant_replaces_the_workflow_level_one() -> None:
    narrowed = (
        "permissions: write-all\n"
        f"jobs:\n  scan:\n    permissions:\n      contents: read\n    uses: {WORKFLOW}\n"
    )
    widened = (
        "permissions:\n  contents: read\n"
        f"jobs:\n  scan:\n    permissions: write-all\n    uses: {WORKFLOW}\n"
    )

    assert any(
        "must grant security-events: write" in problem
        for problem in reference_problems("snippet.yml", narrowed)
    )
    assert reference_problems("snippet.yml", widened) == []
