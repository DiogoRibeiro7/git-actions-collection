#!/usr/bin/env python3
"""Preflight checks for repository releases."""
from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
from pathlib import Path
import re
import subprocess
import tomllib

SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[.-][0-9A-Za-z.-]+)?$")
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


def validate_release(
    *,
    root: Path,
    version: str,
    default_branch: str,
    prerelease: bool,
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

    candidates = list(paths) if paths is not None else tracked_paths(root)
    stale = stale_branch_references(candidates)
    if stale:
        errors.append(
            "retired develop-branch references remain in tracked content: "
            + ", ".join(sorted(stale))
        )

    return errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--default-branch", required=True)
    parser.add_argument("--prerelease", action="store_true")
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
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Release preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
