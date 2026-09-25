#!/usr/bin/env python3
"""Check that every pinned action SHA is the commit of a release tag.

The offline pinning tests only see 40 hexadecimal characters. A SHA that does
not exist, an annotated tag object, or an untagged branch commit passes them,
yet the first fails every caller at runtime and the others are not reviewed
releases. This script lists each action repository's tags with
`git ls-remote`, which needs no token, and reports every pin that is not the
commit a tag points to.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import subprocess
from typing import Any

import yaml

COMMIT_SHA = re.compile(r"[0-9a-f]{40}")
SOURCES = (
    ".github/workflows/*.y*ml",
    ".github/actions/*/action.y*ml",
    "examples/**/.github/workflows/*.y*ml",
)

Pins = dict[tuple[str, str], set[str]]
Tags = tuple[dict[str, list[str]], set[str]]


def _uses(data: Mapping[str, Any]) -> Iterator[str]:
    for job in (data.get("jobs") or {}).values():
        if isinstance(job.get("uses"), str):
            yield job["uses"]
        yield from (step["uses"] for step in job.get("steps", []) if "uses" in step)
    yield from (
        step["uses"] for step in (data.get("runs") or {}).get("steps", []) if "uses" in step
    )


def pinned_actions(root: Path) -> Pins:
    """Map each (owner/repo, commit SHA) pin to the files that use it."""
    pins: Pins = {}
    for pattern in SOURCES:
        for path in sorted(root.glob(pattern)):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for uses in _uses(data):
                action, _, ref = uses.rpartition("@")
                if uses.startswith(("./", "docker://")) or not COMMIT_SHA.fullmatch(ref):
                    continue
                repository = "/".join(action.split("/")[:2])
                pins.setdefault((repository, ref), set()).add(path.relative_to(root).as_posix())
    return pins


def parse_tags(ls_remote: str) -> Tags:
    """Return the commits tags point to (with their names) and annotated tag object SHAs."""
    direct: dict[str, str] = {}
    peeled: dict[str, str] = {}
    for line in ls_remote.splitlines():
        sha, _, ref = line.partition("\t")
        name = ref.removeprefix("refs/tags/")
        if name.endswith("^{}"):
            peeled[name[: -len("^{}")]] = sha
        else:
            direct[name] = sha

    commits: dict[str, list[str]] = {}
    tag_objects: set[str] = set()
    for name, sha in direct.items():
        if name in peeled:
            tag_objects.add(sha)
            sha = peeled[name]
        commits.setdefault(sha, []).append(name)
    return commits, tag_objects


def list_tags(repository: str) -> str | None:
    """Return `git ls-remote --tags` output, or None when the repository is unreachable."""
    result = subprocess.run(
        ["git", "ls-remote", "--tags", f"https://github.com/{repository}.git"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    return result.stdout if result.returncode == 0 else None


def problems(pins: Pins, tags_of: Callable[[str], str | None] = list_tags) -> list[str]:
    """Describe every pin that is not the commit of a release tag."""
    repositories = sorted({repository for repository, _ in pins})
    with ThreadPoolExecutor(max_workers=8) as pool:
        outputs = dict(zip(repositories, pool.map(tags_of, repositories)))
    tags = {
        repository: None if output is None else parse_tags(output)
        for repository, output in outputs.items()
    }

    found: list[str] = []
    for (repository, sha), files in sorted(pins.items()):
        known = tags[repository]
        if known is None:
            reason = "repository not found"
        elif sha in known[0]:
            continue
        elif sha in known[1]:
            reason = "is an annotated tag object; pin the commit it points to"
        else:
            reason = "is not the commit of any tag"
        found.append(f"{repository}@{sha} {reason} ({', '.join(sorted(files))})")
    return found


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    args = parser.parse_args(argv)

    pins = pinned_actions(args.root)
    found = problems(pins)
    if found:
        print("Action pins that are not release commits:")
        print("\n".join(f"  - {line}" for line in found))
        return 1
    print(f"All {len(pins)} action pins are release commits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
