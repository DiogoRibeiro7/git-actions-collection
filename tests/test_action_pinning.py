"""Every executable action reference must be immutable.

A tag or branch can be moved to different code after review, and a mistyped tag
(for example `actions/checkout@5`) fails every caller at runtime. Third-party
actions therefore use full commit SHAs and Docker actions use image digests.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
import re

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SELF = "DiogoRibeiro7/git-actions-collection/"
COMMIT_SHA = re.compile(r"[0-9a-f]{40}")


def _references(path: Path) -> Iterator[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for job in (data.get("jobs") or {}).values():
        if isinstance(job.get("uses"), str):
            yield job["uses"]
        yield from (step["uses"] for step in job.get("steps", []) if "uses" in step)
    yield from (
        step["uses"] for step in (data.get("runs") or {}).get("steps", []) if "uses" in step
    )


def pinning_problem(uses: str, *, consumer_example: bool = False) -> str | None:
    """Explain why a `uses:` reference is not immutable, or return None."""
    if uses.startswith("./"):
        return None
    if uses.startswith("docker://"):
        return None if "@sha256:" in uses else "Docker image without an @sha256 digest"
    if uses.startswith(SELF):
        if consumer_example:
            # Consumer examples document the supported moving major tag.
            return None if uses.endswith("@v1") else "consumer examples should use @v1"
        return "reference this repository's own workflows and actions with ./ paths"
    _, separator, ref = uses.rpartition("@")
    if not separator:
        return "no ref; pin a full commit SHA"
    if not COMMIT_SHA.fullmatch(ref):
        return f"mutable ref {ref!r}; pin a full 40-character commit SHA"
    return None


def _problems(paths: list[Path], *, consumer_example: bool) -> list[str]:
    return [
        f"{path.relative_to(ROOT).as_posix()}: {uses} ({problem})"
        for path in paths
        for uses in _references(path)
        if (problem := pinning_problem(uses, consumer_example=consumer_example))
    ]


def test_workflows_and_composite_actions_pin_every_external_action() -> None:
    paths = [
        *sorted((ROOT / ".github" / "workflows").glob("*.y*ml")),
        *sorted((ROOT / ".github" / "actions").glob("*/action.y*ml")),
    ]

    problems = _problems(paths, consumer_example=False)

    assert paths
    assert not problems, "Mutable action references:\n" + "\n".join(problems)


def test_consumer_examples_pin_third_party_actions() -> None:
    paths = sorted((ROOT / "examples").glob("**/.github/workflows/*.y*ml"))

    problems = _problems(paths, consumer_example=True)

    assert paths
    assert not problems, "Mutable action references:\n" + "\n".join(problems)


def test_each_file_pins_one_commit_per_action_repository() -> None:
    """Sub-actions of one repository, such as CodeQL init/autobuild/analyze, move together."""
    paths = [
        *sorted((ROOT / ".github" / "workflows").glob("*.y*ml")),
        *sorted((ROOT / ".github" / "actions").glob("*/action.y*ml")),
        *sorted((ROOT / "examples").glob("**/.github/workflows/*.y*ml")),
    ]
    problems: list[str] = []

    for path in paths:
        refs: dict[str, set[str]] = {}
        for uses in _references(path):
            if uses.startswith(("./", "docker://")):
                continue
            action, _, ref = uses.rpartition("@")
            refs.setdefault("/".join(action.split("/")[:2]), set()).add(ref)
        problems += [
            f"{path.relative_to(ROOT).as_posix()}: {repository} at {sorted(pinned)}"
            for repository, pinned in refs.items()
            if len(pinned) > 1
        ]

    assert not problems, "Actions pinned to several commits:\n" + "\n".join(problems)


SHA = "fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09"


@pytest.mark.parametrize(
    ("uses", "consumer_example", "problem"),
    [
        (f"actions/checkout@{SHA}", False, None),
        (f"github/codeql-action/init@{SHA}", False, None),
        ("./.github/actions/setup-yarn", False, None),
        ("docker://alpine@sha256:" + "a" * 64, False, None),
        ("actions/checkout@v5", False, "mutable ref 'v5'"),
        ("actions/checkout@5", False, "mutable ref '5'"),
        ("actions/dependency-review-action@main", False, "mutable ref 'main'"),
        ("dtolnay/rust-toolchain@stable", False, "mutable ref 'stable'"),
        (f"actions/checkout@{SHA[:7]}", False, "mutable ref 'fbc6f39'"),
        ("actions/checkout", False, "no ref"),
        ("docker://alpine:3.20", False, "without an @sha256 digest"),
        (f"{SELF}.github/workflows/rust-ci.yml@v1", False, "with ./ paths"),
        (f"{SELF}.github/workflows/rust-ci.yml@v1", True, None),
        (f"{SELF}.github/workflows/rust-ci.yml@main", True, "should use @v1"),
    ],
)
def test_pinning_rules(uses: str, consumer_example: bool, problem: str | None) -> None:
    result = pinning_problem(uses, consumer_example=consumer_example)

    if problem is None:
        assert result is None
    else:
        assert result is not None and problem in result
