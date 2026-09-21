#!/usr/bin/env python3
"""Generate starter GitHub Actions workflows.

This helper reduces manual setup by emitting opinionated workflow files for
supported languages. Configurations are validated before any files are written
and sensible defaults are applied for branch names and output locations.
"""
from __future__ import annotations

import argparse
import os
import sys

from scripts._lib.workflows import (
    CHECKOUT_REF,
    SETUP_NODE_REF,
    SETUP_PYTHON_REF,
    node_workflow,
    python_workflow,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a GitHub Actions workflow")
    parser.add_argument(
        "language",
        choices=["python", "node"],
        help="Select which workflow to generate",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path for output file (default: .github/workflows/<language>-ci.yml)",
    )
    parser.add_argument(
        "-b",
        "--branch",
        default="main",
        help="Default branch to trigger on (default: main)",
    )
    args = parser.parse_args()

    output = args.output or os.path.join(
        ".github", "workflows", f"{args.language}-ci.yml"
    )
    os.makedirs(os.path.dirname(output), exist_ok=True)

    if os.path.exists(output):
        parser.error(f"{output} already exists")

    if args.language == "python":
        content = python_workflow(args.branch)
    else:
        content = node_workflow(args.branch)

    try:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(content)
    except OSError as exc:  # pragma: no cover - filesystem errors
        print(f"error: unable to write {output}: {exc}", file=sys.stderr)
        return 1

    print(f"workflow written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
