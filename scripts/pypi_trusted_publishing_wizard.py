#!/usr/bin/env python3
"""Interactive wizard to set up PyPI trusted publishing."""
from __future__ import annotations
import os
import sys
import shutil
import textwrap
import subprocess

WORKFLOW_TEMPLATE = """name: Publish to PyPI
on:
  release:
    types: [published]
jobs:
  publish:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/publish-to-pypi.yml@develop
    with:
      python-version: '3.12'
"""

def check_prerequisites() -> None:
    if shutil.which("gh") is None:
        print(
            "Error: GitHub CLI 'gh' is required. Install from https://cli.github.com/ and run 'gh auth login'.",
            file=sys.stderr,
        )
        sys.exit(1)

def guess_repo() -> str:
    try:
        return subprocess.check_output(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            text=True,
        ).strip()
    except Exception:
        return input("GitHub repository (owner/repo): ").strip()

def main() -> None:
    check_prerequisites()
    print("PyPI Trusted Publishing Setup Wizard\n")
    repo = guess_repo()
    project = input("PyPI project name: ").strip()
    workflow_path = os.path.join(".github", "workflows", "publish-to-pypi.yml")
    os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
    if os.path.exists(workflow_path):
        overwrite = input(f"{workflow_path} exists. Overwrite? [y/N]: ").strip().lower()
        if overwrite != "y":
            print("Aborted - existing workflow preserved.")
            return
    with open(workflow_path, "w", encoding="utf-8") as fh:
        fh.write(WORKFLOW_TEMPLATE)
    print(f"Created {workflow_path}")
    print("\nNext steps:")
    print(
        textwrap.dedent(
            f"""
            1. On PyPI, add a trusted publisher for project '{project}'.
               Link it to the workflow '{workflow_path}' in repository '{repo}'.
            2. Create a GitHub release to trigger publishing.
            3. For troubleshooting, see docs/pypi-trusted-publishing.md.
            """
        ).strip()
    )

if __name__ == "__main__":
    main()
