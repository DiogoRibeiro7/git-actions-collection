from pathlib import Path
from typing import Any

import yaml

# actions/labeler v5+ labels list match objects; these keys are the only valid ones.
MATCH_OBJECT_KEYS = {"changed-files", "head-branch", "base-branch", "all", "any"}
TOP_LEVEL_OPTIONS = {"changed-files-labels-limit", "max-files-changed"}


def _load_workflow() -> dict[str, Any]:
    """Load the reusable PR policy workflow."""
    path = Path(".github/workflows/pr-policy.yml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _step(name: str) -> dict[str, Any]:
    steps = _load_workflow()["jobs"]["label-and-size"]["steps"]
    return next(step for step in steps if step.get("name") == name)


def test_pr_policy_only_writes_pull_request_labels() -> None:
    assert _load_workflow()["permissions"] == {"contents": "read", "pull-requests": "write"}


def test_pr_policy_enforces_the_template_from_the_collection_checkout() -> None:
    step = _step("Enforce PR template")

    assert step["uses"] == "./.git-actions-collection/.github/actions/pr-template-enforcer"


def test_pr_policy_labels_every_pull_request_by_size() -> None:
    step = _step("Label PR size")

    assert "if" not in step
    assert step["with"]["GITHUB_TOKEN"] == "${{ secrets.GITHUB_TOKEN }}"


def test_pr_policy_labels_paths_only_when_the_caller_has_a_config() -> None:
    """labeler v6 fails without a config, so callers opt in by adding one."""
    step = _step("Label PR by changed paths")

    assert step["if"] == "hashFiles('.github/labeler.yml') != ''"
    assert step["uses"].startswith("actions/labeler@")
    assert step["with"]["repo-token"] == "${{ secrets.GITHUB_TOKEN }}"


def test_repository_labeler_config_uses_v5_match_objects() -> None:
    """The pre-v5 format (a label mapped straight to globs) is rejected by labeler v6."""
    config = yaml.safe_load(Path(".github/labeler.yml").read_text(encoding="utf-8"))

    assert config
    for label, rules in config.items():
        if label in TOP_LEVEL_OPTIONS:
            continue
        assert isinstance(rules, list) and rules, label
        for rule in rules:
            assert isinstance(rule, dict), f"{label}: {rule!r} is a pre-v5 glob"
            assert set(rule) <= MATCH_OBJECT_KEYS, f"{label}: {sorted(rule)}"
