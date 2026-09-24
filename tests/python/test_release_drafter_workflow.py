from pathlib import Path
from typing import Any

import yaml

# release-drafter v7.7.0; v7 dropped the GITHUB_TOKEN env variable and several config keys.
RELEASE_DRAFTER = "release-drafter/release-drafter@34d80673e067bdc0c24568d3af899c216adcfaa9"
REMOVED_IN_V7 = {"autolabeler", "include-pre-releases", "references"}


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Release Drafter workflow."""
    path = Path(".github/workflows/release-drafter.yml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _drafter_step() -> dict[str, Any]:
    steps = _load_workflow()["jobs"]["update"]["steps"]
    return next(step for step in steps if step.get("uses", "").startswith("release-drafter/"))


def test_release_drafter_requests_only_draft_release_permissions() -> None:
    """Drafting a release writes contents and reads merged pull requests."""
    assert _load_workflow()["permissions"] == {"contents": "write", "pull-requests": "read"}


def test_release_drafter_uses_the_pinned_v7_action() -> None:
    assert _drafter_step()["uses"] == RELEASE_DRAFTER


def test_release_drafter_relies_on_the_v7_token_input() -> None:
    """v7 ignores the GITHUB_TOKEN env variable; its token input defaults to github.token."""
    step = _drafter_step()

    assert "GITHUB_TOKEN" not in (step.get("env") or {})
    assert step.get("with", {}).get("token", "${{ github.token }}") == "${{ github.token }}"
    assert step["with"]["config-name"] == "release-drafter.yml"


def test_repository_release_drafter_config_avoids_keys_removed_in_v7() -> None:
    """v7 no longer reads these keys, so they would be silently ignored."""
    config = yaml.safe_load(Path(".github/release-drafter.yml").read_text(encoding="utf-8"))

    assert REMOVED_IN_V7.isdisjoint(config)
