#!/usr/bin/env python3
"""Migrate GitHub starter workflows to this collection's reusable workflows."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
import os
import sys

from scripts._lib.migration import (
    convert,
    explain,
    load_workflow,
    migration_report,
    plan_migration,
    render_migration,
)

__all__ = ["convert", "main"]


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", help="Path to GitHub starter workflow")
    parser.add_argument(
        "--output", "-o", help="Where to write converted workflow (stdout if omitted)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explain the migration and print the workflow without writing any file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable report of the migration instead of the workflow",
    )
    parser.add_argument(
        "--default-branch",
        default="main",
        help="Branch that replaces the $default-branch placeholder of GitHub's starter templates",
    )
    args = parser.parse_args(argv)

    with open(args.workflow, "r", encoding="utf-8") as fh:
        plan = plan_migration(load_workflow(fh.read()), args.default_branch)
    migrated = render_migration(plan) if plan.uses else None

    written = None
    if migrated and args.output and not args.dry_run:
        if os.path.exists(args.output):
            raise SystemExit(f"Refusing to overwrite existing file: {args.output}")
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(migrated)
        written = args.output

    if args.json:
        report = migration_report(plan, source=args.workflow, output=written, migrated=migrated)
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    elif args.dry_run:
        sys.stdout.write(explain(plan))
        if migrated:
            sys.stdout.write("\n" + migrated)
        sys.stdout.write("No files were written (dry run).\n")
    elif migrated and not written:
        sys.stdout.write(migrated)

    if migrated is None:
        if not (args.json or args.dry_run):
            sys.stderr.write(explain(plan))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
