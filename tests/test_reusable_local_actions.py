"""Reusable workflows must not rely on the caller's checkout for this collection's actions.

A step-level `uses: ./path` in a reusable workflow resolves inside the caller's
workspace, where this collection's composite actions do not exist. Such steps
must use a checkout of this collection at `job.workflow_sha`, the exact commit of
the reusable workflow. Calling a workflow file from a step is never valid.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ".git-actions-collection"
COLLECTION_CHECKOUT = {
    "repository": "${{ job.workflow_repository }}",
    "ref": "${{ job.workflow_sha }}",
    "path": COLLECTION,
}


def _is_reusable(workflow: dict[str, Any]) -> bool:
    triggers = workflow.get("on") or workflow.get(True) or {}
    return isinstance(triggers, dict) and "workflow_call" in triggers


def local_action_problems(workflow: dict[str, Any]) -> list[str]:
    """Explain which steps would resolve a local action in the caller's checkout."""
    problems: list[str] = []
    for job_name, job in (workflow.get("jobs") or {}).items():
        has_collection = False
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if uses.startswith("actions/checkout@"):
                with_ = step.get("with") or {}
                if all(with_.get(key) == value for key, value in COLLECTION_CHECKOUT.items()):
                    has_collection = True
            if uses.startswith("./") and uses.endswith((".yml", ".yaml")):
                problems.append(f"job {job_name!r} calls workflow {uses} from a step")
            elif uses.startswith("./") and not uses.startswith(f"./{COLLECTION}/"):
                problems.append(
                    f"job {job_name!r} uses {uses}, which resolves in the caller's checkout"
                )
            elif uses.startswith(f"./{COLLECTION}/") and not has_collection:
                problems.append(
                    f"job {job_name!r} uses {uses} before checking out the collection "
                    "at job.workflow_sha"
                )
    return problems


def test_reusable_workflows_run_collection_actions_from_their_own_commit() -> None:
    problems = [
        f"{path.name}: {problem}"
        for path in sorted((ROOT / ".github" / "workflows").glob("*.y*ml"))
        if _is_reusable(workflow := yaml.safe_load(path.read_text(encoding="utf-8")))
        for problem in local_action_problems(workflow)
    ]

    assert not problems, "\n".join(problems)


CHECKOUT = {"uses": "actions/checkout@" + "a" * 40, "with": dict(COLLECTION_CHECKOUT)}
ACTION = {"uses": f"./{COLLECTION}/.github/actions/python-lint"}


@pytest.mark.parametrize(
    ("steps", "problem"),
    [
        ([CHECKOUT, ACTION], None),
        ([{"uses": "actions/setup-python@" + "b" * 40}], None),
        ([{"uses": "./.github/actions/python-lint"}], "resolves in the caller's checkout"),
        ([ACTION, CHECKOUT], "before checking out the collection"),
        (
            [{"uses": "actions/checkout@" + "a" * 40, "with": {"path": COLLECTION}}, ACTION],
            "before checking out the collection",
        ),
        ([{"uses": "./.github/workflows/runner.yml"}], "calls workflow"),
    ],
)
def test_local_action_rules(steps: list[dict[str, Any]], problem: str | None) -> None:
    problems = local_action_problems({"jobs": {"lint": {"steps": steps}}})

    if problem is None:
        assert problems == []
    else:
        assert any(problem in line for line in problems), problems
