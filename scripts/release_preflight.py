#!/usr/bin/env python3
"""Preflight checks for repository releases.

Run it from the repository root as ``python -m scripts.release_preflight`` so the
``scripts`` package resolves.
"""
from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
import json
from pathlib import Path
import re
import subprocess
import tomllib
from typing import Any

from scripts.interface_snapshot import SNAPSHOT, compare, current_interfaces

SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[.-][0-9A-Za-z.-]+)?$")
VERSION_CORE = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)")
STABLE_TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
LEVEL_TWO_HEADING = re.compile(r"^## +(.+?)\s*$", re.MULTILINE)
STALE_BRANCH_FRAGMENTS = (
    "@" + "develop",
    "refs/heads/" + "develop",
    "branches: [" + "develop" + "]",
    "branches: [ " + "develop" + " ]",
)


def project_version(root: Path) -> str:
    """Read the PEP 621 project version."""
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def tracked_paths(root: Path) -> list[Path]:
    """Return files tracked by Git."""
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [root / relative for relative in completed.stdout.split("\0") if relative]


def stale_branch_references(paths: Iterable[Path]) -> list[str]:
    """Return tracked text files that still encode the retired branch model."""
    offenders: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(fragment in content for fragment in STALE_BRANCH_FRAGMENTS):
            offenders.append(str(path))
    return offenders


def changelog_errors(root: Path, version: str) -> list[str]:
    """Require a dated section for the release and no entries left unreleased."""
    path = root / "CHANGELOG.md"
    if not path.is_file():
        return ["CHANGELOG.md is missing"]

    headings = LEVEL_TWO_HEADING.findall(path.read_text(encoding="utf-8"))
    dated = re.compile(re.escape(version) + r" - [0-9]{4}-[0-9]{2}-[0-9]{2}")
    errors: list[str] = []
    if not any(dated.fullmatch(heading) for heading in headings):
        errors.append(f"CHANGELOG.md has no '## {version} - YYYY-MM-DD' section")
    if any(heading.strip("[]").lower() == "unreleased" for heading in headings):
        errors.append(
            "CHANGELOG.md still has an Unreleased section; "
            "move its entries into the release section"
        )
    return errors


def _core(version: str) -> tuple[int, int, int]:
    match = VERSION_CORE.match(version)
    if match is None:
        raise ValueError(f"not a semantic version: {version!r}")
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def previous_release(tags: Iterable[str], version: str) -> str | None:
    """Return the newest stable release tag older than ``version``."""
    releases = {_core(tag[1:]): tag for tag in tags if STABLE_TAG.fullmatch(tag)}
    older = [core for core in releases if core < _core(version)]
    return releases[max(older)] if older else None


def release_tags(root: Path) -> list[str]:
    """Return the repository's version tags."""
    completed = subprocess.run(
        ["git", "tag", "--list", "v*"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.split()


def released_interfaces(root: Path, tag: str) -> dict[str, Any] | None:
    """Return the supported-interface snapshot recorded at ``tag``, if it has one."""
    completed = subprocess.run(
        ["git", "show", f"{tag}:{SNAPSHOT.as_posix()}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        return None
    interfaces: dict[str, Any] = json.loads(completed.stdout)
    return interfaces


def interface_errors(
    root: Path, version: str, *, allow_breaking: bool, tags: Iterable[str]
) -> list[str]:
    """Check supported interfaces against their snapshot and the previous release.

    The snapshot must be current because the next release compares against the
    copy this release tags. Within a major version, a breaking change since the
    previous release fails unless the releaser accepts it as one of the
    exceptions SUPPORT.md allows.
    """
    current = current_interfaces(root)
    snapshot = root / SNAPSHOT
    recorded = json.loads(snapshot.read_text(encoding="utf-8")) if snapshot.is_file() else {}
    errors: list[str] = []
    if any(compare(recorded, current)):
        errors.append(
            f"{SNAPSHOT.as_posix()} does not match the supported workflows and actions; "
            "run python scripts/interface_snapshot.py --check"
        )

    previous = previous_release(tags, version)
    if previous is None or _core(previous[1:])[0] != _core(version)[0]:
        # A new major version may change supported interfaces.
        return errors
    released = released_interfaces(root, previous)
    if released is None:
        # Releases made before the snapshot existed have nothing to compare.
        return errors

    breaking, _ = compare(released, current)
    if allow_breaking:
        for change in breaking:
            print(f"Accepted breaking change since {previous}: {change}")
    elif breaking:
        errors.extend(f"breaking change since {previous}: {change}" for change in breaking)
        errors.append(
            "supported interfaces must stay compatible within a major version; "
            "release a new major version, or pass --allow-breaking-changes when "
            "each change is an exception that SUPPORT.md allows"
        )
    return errors


def validate_release(
    *,
    root: Path,
    version: str,
    default_branch: str,
    prerelease: bool,
    allow_breaking: bool = False,
    paths: Iterable[Path] | None = None,
) -> list[str]:
    """Validate repository state before a release is created."""
    errors: list[str] = []

    if SEMVER.fullmatch(version) is None:
        errors.append("version must be a semantic version without the v prefix")

    if default_branch != "main":
        errors.append(f"GitHub default branch must be main, found {default_branch!r}")

    if not prerelease and project_version(root) != version:
        errors.append(
            "pyproject.toml version "
            f"{project_version(root)!r} does not match stable release {version!r}"
        )

    if not prerelease:
        errors.extend(changelog_errors(root, version))

    candidates = list(paths) if paths is not None else tracked_paths(root)
    stale = stale_branch_references(candidates)
    if stale:
        errors.append(
            "retired develop-branch references remain in tracked content: "
            + ", ".join(sorted(stale))
        )

    if SEMVER.fullmatch(version) is not None:
        errors.extend(
            interface_errors(
                root, version, allow_breaking=allow_breaking, tags=release_tags(root)
            )
        )

    return errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--default-branch", required=True)
    parser.add_argument("--prerelease", action="store_true")
    parser.add_argument(
        "--allow-breaking-changes",
        action="store_true",
        help="accept breaking changes to supported interfaces since the previous "
        "release; only for the exceptions SUPPORT.md allows",
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run release preflight checks."""
    args = parse_args(argv)
    root = args.root.resolve()
    errors = validate_release(
        root=root,
        version=args.version,
        default_branch=args.default_branch,
        prerelease=args.prerelease,
        allow_breaking=args.allow_breaking_changes,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Release preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
