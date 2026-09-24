"""Workflow token permissions must be explicit and scoped to the jobs that use them.

A job without a `permissions` block inherits the repository's default token,
which can be write access to everything. `write-all` and `read-all` hide what a
workflow really needs, and a workflow-level write reaches every job, including
jobs that never use it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def permission_problems(workflow: dict[str, Any]) -> list[str]:
    """Explain how a workflow's token permissions are broader or less explicit than needed."""
    problems: list[str] = []
    default = workflow.get("permissions")
    jobs = workflow.get("jobs") or {}

    blocks = [
        ("workflow", default),
        *((f"job {name!r}", job.get("permissions")) for name, job in jobs.items()),
    ]
    for holder, block in blocks:
        if isinstance(block, str):
            problems.append(f"{holder} uses {block!r}; list the scopes it needs")

    if default is None:
        implicit = [name for name, job in jobs.items() if "permissions" not in job]
        if implicit:
            problems.append(
                "jobs "
                + ", ".join(repr(name) for name in implicit)
                + " inherit the repository default token; declare permissions"
            )
    elif isinstance(default, dict) and len(jobs) > 1:
        writes = sorted(scope for scope, level in default.items() if level == "write")
        if writes:
            problems.append(
                f"workflow-level {', '.join(writes)}: write reaches all {len(jobs)} jobs; "
                "grant it on the jobs that need it"
            )
    return problems


def test_workflows_declare_least_privilege_permissions() -> None:
    problems = [
        f"{path.name}: {problem}"
        for path in sorted((ROOT / ".github" / "workflows").glob("*.y*ml"))
        for problem in permission_problems(yaml.safe_load(path.read_text(encoding="utf-8")))
    ]

    assert not problems, "Workflow permissions are too broad:\n" + "\n".join(problems)


@pytest.mark.parametrize(
    ("workflow", "problem"),
    [
        ({"permissions": {"contents": "read"}, "jobs": {"a": {}, "b": {}}}, None),
        ({"permissions": {}, "jobs": {"a": {}}}, None),
        ({"jobs": {"a": {"permissions": {"contents": "read"}}}}, None),
        ({"permissions": {"contents": "write"}, "jobs": {"only": {}}}, None),
        (
            {
                "permissions": {"contents": "read"},
                "jobs": {"a": {}, "b": {"permissions": {"contents": "read", "id-token": "write"}}},
            },
            None,
        ),
        ({"jobs": {"a": {}}}, "jobs 'a' inherit the repository default token"),
        (
            {"jobs": {"a": {"permissions": {"contents": "read"}}, "b": {}}},
            "jobs 'b' inherit the repository default token",
        ),
        ({"permissions": "write-all", "jobs": {"a": {}}}, "workflow uses 'write-all'"),
        (
            {"permissions": {}, "jobs": {"a": {"permissions": "read-all"}}},
            "job 'a' uses 'read-all'",
        ),
        (
            {"permissions": {"contents": "read", "id-token": "write"}, "jobs": {"a": {}, "b": {}}},
            "workflow-level id-token: write reaches all 2 jobs",
        ),
    ],
)
def test_permission_rules(workflow: dict[str, Any], problem: str | None) -> None:
    problems = permission_problems(workflow)

    if problem is None:
        assert problems == []
    else:
        assert any(problem in line for line in problems), problems
