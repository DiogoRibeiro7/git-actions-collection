from __future__ import annotations

from pathlib import Path
import re

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / ".github" / "support-matrix.yml"
SHA_REF = re.compile(r"^[0-9a-f]{40}$")


def _load_matrix() -> dict:
    return yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8"))


def test_all_composite_actions_are_classified_once() -> None:
    matrix = _load_matrix()
    actions = matrix["composite_actions"]

    classified = [
        name
        for tier in ("supported", "reference", "experimental")
        for name in actions[tier]
    ]
    actual = sorted(
        path.name
        for path in (ROOT / ".github" / "actions").iterdir()
        if path.is_dir() and (path / "action.yml").exists()
    )

    assert len(classified) == len(set(classified)), "composite action appears in multiple tiers"
    assert sorted(classified) == actual


def test_supported_composite_actions_have_contract_tests() -> None:
    matrix = _load_matrix()
    exceptions = {
        "check-imports": "test_check_imports_contract.bats",
        "smart-dependency-update": "test_smart_dependency_update_contract.bats",
    }

    for name in matrix["composite_actions"]["supported"]:
        filename = exceptions.get(name, f"test_{name.replace('-', '_')}.bats")
        path = ROOT / "tests" / "bash" / "actions" / filename
        assert path.exists(), f"supported action {name} lacks contract test {path}"


# Supported actions whose only coverage is still the Bats contract test with fake
# tools. Remove each one when an internal workflow starts running it; the set must
# only shrink.
AWAITING_RUNNER_SELF_TEST = {
    "apm-integration",
    "pr-template-enforcer",
}
LOCAL_ACTION = re.compile(r"uses:\s*\./(?:[\w.-]+/)?\.github/actions/([\w-]+)")
LOCAL_WORKFLOW = re.compile(r"uses:\s*\./\.github/workflows/([\w.-]+\.ya?ml)")


def _actions_run_by_internal_workflows(matrix: dict) -> set[str]:
    """Actions that an internal workflow runs, directly or through a workflow it calls."""
    workflows = ROOT / ".github" / "workflows"
    run: set[str] = set()
    for name in matrix["workflows"]["internal"]:
        text = (workflows / name).read_text(encoding="utf-8")
        run.update(LOCAL_ACTION.findall(text))
        for called in LOCAL_WORKFLOW.findall(text):
            run.update(LOCAL_ACTION.findall((workflows / called).read_text(encoding="utf-8")))
    return run


def test_supported_composite_actions_run_on_a_real_runner() -> None:
    """Contract tests replace every tool with a fake, so they cannot notice a
    changed upstream tool or a runner difference; a self-test on a runner can."""
    matrix = _load_matrix()
    supported = set(matrix["composite_actions"]["supported"])
    run = _actions_run_by_internal_workflows(matrix)

    assert not supported - run - AWAITING_RUNNER_SELF_TEST, (
        "supported actions without a real-runner self-test: "
        f"{sorted(supported - run - AWAITING_RUNNER_SELF_TEST)}"
    )
    assert not AWAITING_RUNNER_SELF_TEST & run, (
        "these actions now have a self-test; remove them from AWAITING_RUNNER_SELF_TEST: "
        f"{sorted(AWAITING_RUNNER_SELF_TEST & run)}"
    )
    assert AWAITING_RUNNER_SELF_TEST <= supported


def _actions_named_in_sentence(text: str, marker: str, actions: set[str]) -> set[str] | None:
    """Return the actions named in the sentence containing *marker*, or None."""
    for sentence in re.split(r"(?<=\.)\s+", " ".join(text.split())):
        if marker in sentence:
            return set(re.findall(r"`([\w-]+)`", sentence)) & actions
    return None


@pytest.mark.parametrize(
    ("document", "marker"),
    [
        ("SUPPORT.md", "are still waiting for that self-test"),
        ("ROADMAP.md", "still need a real-runner job"),
    ],
)
def test_docs_name_the_actions_still_awaiting_a_self_test(document: str, marker: str) -> None:
    """Both documents repeat AWAITING_RUNNER_SELF_TEST by hand, so keep them equal."""
    supported = set(_load_matrix()["composite_actions"]["supported"])
    named = _actions_named_in_sentence(
        (ROOT / document).read_text(encoding="utf-8"), marker, supported
    )

    if AWAITING_RUNNER_SELF_TEST:
        assert named == AWAITING_RUNNER_SELF_TEST, (
            f"{document} must name exactly the actions still awaiting a self-test: "
            f"{sorted(AWAITING_RUNNER_SELF_TEST)}"
        )
    else:
        assert named is None, f"every action has a self-test; remove the sentence from {document}"


def test_supported_composite_actions_pin_external_dependencies() -> None:
    matrix = _load_matrix()

    for name in matrix["composite_actions"]["supported"]:
        path = ROOT / ".github" / "actions" / name / "action.yml"
        document = yaml.safe_load(path.read_text(encoding="utf-8"))

        for step in document.get("runs", {}).get("steps", []):
            uses = step.get("uses")
            if not isinstance(uses, str):
                continue
            if uses.startswith("./") or uses.startswith("DiogoRibeiro7/git-actions-collection/"):
                continue

            assert "@" in uses, f"{path}: external action reference has no ref: {uses}"
            _, ref = uses.rsplit("@", 1)
            assert SHA_REF.fullmatch(ref), (
                f"{path}: supported actions must pin external dependencies to a 40-char SHA: {uses}"
            )


def test_all_workflows_are_classified_once() -> None:
    matrix = _load_matrix()
    workflows = matrix["workflows"]

    supported = list(workflows["supported"].keys())
    classified = (
        supported
        + workflows["reference"]
        + workflows["experimental"]
        + workflows["internal"]
    )
    actual = sorted(path.name for path in (ROOT / ".github" / "workflows").glob("*.yml"))

    assert len(classified) == len(set(classified)), "workflow appears in multiple support tiers"
    assert sorted(classified) == actual


def test_supported_workflow_evidence_exists() -> None:
    matrix = _load_matrix()

    for workflow, metadata in matrix["workflows"]["supported"].items():
        workflow_path = ROOT / ".github" / "workflows" / workflow
        assert workflow_path.exists()

        evidence = metadata.get("evidence", [])
        assert evidence, f"supported workflow {workflow} must declare evidence"
        for relative in evidence:
            assert (ROOT / relative).exists(), f"missing support evidence for {workflow}: {relative}"


def test_supported_workflows_pin_external_dependencies() -> None:
    matrix = _load_matrix()

    for workflow in matrix["workflows"]["supported"]:
        path = ROOT / ".github" / "workflows" / workflow
        document = yaml.safe_load(path.read_text(encoding="utf-8"))

        for job in document.get("jobs", {}).values():
            for step in job.get("steps", []):
                uses = step.get("uses")
                if not isinstance(uses, str):
                    continue
                if uses.startswith("./") or uses.startswith("DiogoRibeiro7/git-actions-collection/"):
                    continue

                assert "@" in uses, f"{path}: external action reference has no ref: {uses}"
                _, ref = uses.rsplit("@", 1)
                assert SHA_REF.fullmatch(ref), (
                    f"{path}: supported workflows must pin external dependencies "
                    f"to a 40-char SHA: {uses}"
                )


def test_supported_workflows_declare_permissions() -> None:
    matrix = _load_matrix()

    for workflow in matrix["workflows"]["supported"]:
        path = ROOT / ".github" / "workflows" / workflow
        document = yaml.safe_load(path.read_text(encoding="utf-8"))

        permissions = document.get("permissions")
        assert isinstance(permissions, dict) and permissions, (
            f"{path}: supported workflows must declare explicit top-level permissions"
        )


def test_support_policy_lists_exactly_the_supported_components() -> None:
    """SUPPORT.md repeats the supported tier by hand, so check it against the matrix."""
    matrix = _load_matrix()
    policy = (ROOT / "SUPPORT.md").read_text(encoding="utf-8")
    section = policy.split("\n### Supported\n", 1)[1].split("\n### ", 1)[0]
    workflow_list = section.split("The supported reusable workflows are:", 1)[1]
    workflow_list = workflow_list.strip().split("\n\n", 1)[0]

    assert set(re.findall(r"`([\w.-]+\.yml)`", workflow_list)) == set(
        matrix["workflows"]["supported"]
    ), "Update the supported workflow list in SUPPORT.md to match the support matrix"

    actions = matrix["composite_actions"]
    claim = re.search(r"All (\d+) composite actions are currently supported", section)
    assert claim, "SUPPORT.md no longer states how many composite actions are supported"
    assert int(claim[1]) == len(actions["supported"]), (
        "Update the composite action count in SUPPORT.md"
    )
    assert not actions["reference"] and not actions["experimental"], (
        "SUPPORT.md says all composite actions are supported; reword it"
    )
