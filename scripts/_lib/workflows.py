from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple
from textwrap import dedent

import yaml

CHECKOUT_REF = "08eba0b27e820071cde6df949e0beb9ba4906955"
SETUP_PYTHON_REF = "a26af69be951a213d495a4c3e4e4022e16d87065"
SETUP_NODE_REF = "49933ea5288caeca8642d1e84afbd3f7d6820020"
REPO = "DiogoRibeiro7/gh-actions-collection"


def python_workflow(branch: str) -> str:
    return dedent(
        f"""
        name: Python CI
        "on":
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
    return dedent(
        f"""
        name: Node CI
        "on":
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


def detect_language(workflow: Dict[str, Any]) -> Tuple[str, str]:
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


def generate_migrated(workflow: Dict[str, Any], language: str, version: str) -> str:
    job_name = "ci"
    uses_path = {
        "python": "python-test-matrix.yml",
        "node": "node-ci.yml",
    }[language]
    job: Dict[str, Any] = {"uses": f"{REPO}/.github/workflows/{uses_path}@main"}
    if language == "python" and version:
        job["with"] = {"python-versions": f'["{version}"]'}
    if language == "node" and version:
        job["with"] = {"node-version": str(version)}
    triggers = workflow.get("on") or workflow.get(True) or {}
    workflow_out = {
        "name": workflow.get("name", f"{language.title()} CI"),
        "on": triggers,
        "jobs": {job_name: job},
    }
    return yaml.safe_dump(workflow_out, sort_keys=False)


def convert(content: str) -> str:
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise SystemExit(f"Invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Starter workflow must be a YAML mapping")
    language, version = detect_language(data)
    return generate_migrated(data, language, version)
