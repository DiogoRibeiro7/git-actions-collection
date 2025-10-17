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
from textwrap import dedent

CHECKOUT_REF = "08eba0b27e820071cde6df949e0beb9ba4906955"
SETUP_PYTHON_REF = "a26af69be951a213d495a4c3e4e4022e16d87065"
SETUP_NODE_REF = "49933ea5288caeca8642d1e84afbd3f7d6820020"


def python_workflow(branch: str) -> str:
    """Return a Python CI workflow."""
    return dedent(
        f"""
        name: Python CI
        on:
          push:
            branches: [{branch}]
          pull_request:

        permissions:
          contents: read

        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@{CHECKOUT_REF}
              - uses: actions/setup-python@{SETUP_PYTHON_REF}
                with:
                  python-version: '3.x'
                  cache: pip
              - run: pip install -r requirements.txt
              - run: pytest -q
        """
    ).lstrip()


def node_workflow(branch: str) -> str:
    """Return a Node.js CI workflow using Yarn via Corepack."""
    return dedent(
        f"""
        name: Node CI
        on:
          push:
            branches: [{branch}]
          pull_request:

        permissions:
          contents: read

        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@{CHECKOUT_REF}
              - uses: actions/setup-node@{SETUP_NODE_REF}
                with:
                  node-version: '20'
                  cache: yarn
              - run: corepack enable
              - run: yarn install --immutable
              - run: yarn test
        """
    ).lstrip()


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
