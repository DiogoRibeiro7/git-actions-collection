#!/usr/bin/env python3
"""Migrate GitHub starter workflows to this collection's reusable workflows."""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - handled in _require_yaml
    yaml = None  # type: ignore[assignment]


def _require_yaml() -> None:
    """Ensure PyYAML is available before attempting to parse data."""
    if yaml is None:  # type: ignore[truthy-bool]
        raise SystemExit("PyYAML is required to run this script")

REPO = "DiogoRibeiro7/gh-actions-collection"


def detect_language(workflow: dict[str, Any]) -> Tuple[str, str]:
    """Return language and version from a GitHub starter workflow."""
    jobs = workflow.get("jobs", {})
    for job in jobs.values():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if "actions/setup-python" in uses:
                version = step.get("with", {}).get("python-version", "")
                return "python", version
            if "actions/setup-node" in uses:
                version = step.get("with", {}).get("node-version", "")
                return "node", version
    raise SystemExit("Unable to detect language from starter workflow")


def generate(workflow: dict[str, Any], language: str, version: str) -> str:
    """Generate migrated workflow YAML for the given language."""
    job_name = "ci"
    uses_path = {
        "python": "python-test-matrix.yml",
        "node": "node-ci.yml",
    }[language]
    job: dict[str, Any] = {"uses": f"{REPO}/.github/workflows/{uses_path}@main"}
    if language == "python" and version:
        job["with"] = {"python-versions": f'"[{version!s}]"'}  # will adjust soon
    if language == "node" and version:
        job["with"] = {"node-version": str(version)}
    # fix python versions: version maybe '3.x' or '3.11'
    if language == "python" and version:
        job["with"] = {"python-versions": f'["{version}"]'}
    triggers = workflow.get("on") or workflow.get(True) or {}
    workflow_out = {
        "name": workflow.get("name", f"{language.title()} CI"),
        "on": triggers,
        "jobs": {job_name: job},
    }
    _require_yaml()
    return yaml.safe_dump(workflow_out, sort_keys=False)


def convert(content: str) -> str:
    """Convert starter workflow content to reusable workflow YAML."""
    _require_yaml()
    data = yaml.safe_load(content)
    language, version = detect_language(data)
    return generate(data, language, version)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", help="Path to GitHub starter workflow")
    parser.add_argument(
        "--output", "-o", help="Where to write converted workflow (stdout if omitted)"
    )
    args = parser.parse_args()

    with open(args.workflow, "r", encoding="utf-8") as fh:
        content = fh.read()

    migrated = convert(content)

    if args.output:
        if os.path.exists(args.output):
            raise SystemExit(f"Refusing to overwrite existing file: {args.output}")
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(migrated)
    else:
        sys.stdout.write(migrated)


if __name__ == "__main__":
    main()
