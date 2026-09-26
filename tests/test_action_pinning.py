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


def test_each_action_repository_is_pinned_to_one_commit() -> None:
    """Every pin of an action repository, across workflows, composite actions and
    examples, uses the same commit, so CodeQL init/autobuild/analyze and the copies
    Dependabot updates in each directory move together."""
    paths = [
        *sorted((ROOT / ".github" / "workflows").glob("*.y*ml")),
        *sorted((ROOT / ".github" / "actions").glob("*/action.y*ml")),
        *sorted((ROOT / "examples").glob("**/.github/workflows/*.y*ml")),
    ]
    refs: dict[str, dict[str, set[str]]] = {}

    for path in paths:
        for uses in _references(path):
            if uses.startswith(("./", "docker://")):
                continue
            action, _, ref = uses.rpartition("@")
            repository = "/".join(action.split("/")[:2])
            refs.setdefault(repository, {}).setdefault(ref, set()).add(
                path.relative_to(ROOT).as_posix()
            )

    problems = [
        f"{repository}@{ref}: {', '.join(sorted(files))}"
        for repository, pinned in sorted(refs.items())
        if len(pinned) > 1
        for ref, files in sorted(pinned.items())
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


# Tools are pinned for the same reason as actions: a moving download can change
# what a check does between two runs of the same commit, with nobody reviewing it.
MOVING_TOOL_SOURCES = {
    "downloads a moving 'latest' release": re.compile(r"releases/latest\b"),
    "pipes a downloaded script into a shell": re.compile(
        r"\b(?:curl|wget)\b[^\n]*\|\s*(?:sudo\s+)?(?:ba)?sh\b"
    ),
    "runs a script from a moving branch": re.compile(
        r"raw\.githubusercontent\.com/[^/\s]+/[^/\s]+/(?:main|master|HEAD)/"
    ),
    "asks a setup action for the latest version": re.compile(
        r"^\s*[\w-]*version:\s*['\"]?latest['\"]?\s*$", re.MULTILINE
    ),
}


def tool_source_problems(text: str) -> list[str]:
    """Name each way *text* installs a tool that can change without review."""
    return [problem for problem, pattern in MOVING_TOOL_SOURCES.items() if pattern.search(text)]


def test_workflows_and_actions_install_fixed_tool_releases() -> None:
    paths = [
        *sorted((ROOT / ".github" / "workflows").glob("*.y*ml")),
        *sorted((ROOT / ".github" / "actions").glob("*/action.y*ml")),
        *sorted((ROOT / "examples").glob("**/.github/workflows/*.y*ml")),
    ]

    problems = [
        f"{path.relative_to(ROOT).as_posix()}: {problem}"
        for path in paths
        for problem in tool_source_problems(path.read_text(encoding="utf-8"))
    ]

    assert not problems, "Tools installed from moving sources:\n" + "\n".join(problems)


@pytest.mark.parametrize(
    ("snippet", "problem"),
    [
        (
            "curl -L https://github.com/o/t/releases/latest/download/t.tar.gz | tar -xz",
            "downloads a moving 'latest' release",
        ),
        ("API_URL: https://api.github.com/repos/o/t/releases/latest", "moving 'latest'"),
        ("curl -fsSL https://example.com/install.sh | sudo bash", "into a shell"),
        ("wget -qO- https://example.com/install | sh -s -- -b /usr/local/bin", "into a shell"),
        (
            "curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3",
            "from a moving branch",
        ),
        ("        with:\n          terraform_version: latest\n", "latest version"),
        ("          version: 'latest'\n", "latest version"),
    ],
)
def test_moving_tool_sources_are_detected(snippet: str, problem: str) -> None:
    assert any(problem in found for found in tool_source_problems(snippet))


def test_fixed_tool_releases_pass() -> None:
    fixed = (
        'curl -fsSL -o "$archive" '
        "https://github.com/o/t/releases/download/v1.2.3/t.tar.gz\n"
        'echo "$SHA256  $archive" | sha256sum --check --quiet\n'
        "        with:\n          terraform_version: 1.16.4\n"
        "      default: latest\n"
    )

    assert tool_source_problems(fixed) == []
