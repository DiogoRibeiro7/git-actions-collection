"""release.yml installed semantic-release with `npm i -D`, rewriting the caller's
package.json and lockfile (which @semantic-release/git then committed), at unpinned
versions that no longer worked together."""

import re
from pathlib import Path
from typing import Any

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/release.yml"


def _release_step() -> dict[str, Any]:
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["release"]["steps"]
    return next(step for step in steps if step.get("name") == "Release")


def test_tools_are_installed_outside_the_project() -> None:
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["release"]["steps"]

    assert all("npm i" not in step.get("run", "") for step in steps)
    assert _release_step()["run"].lstrip().startswith("npx --yes")


def test_every_tool_is_pinned_to_an_exact_version() -> None:
    packages = re.findall(r"-p (\S+)", _release_step()["run"])

    assert packages
    assert all(re.fullmatch(r"(@[\w-]+/)?[\w-]+@\d+\.\d+\.\d+", package) for package in packages)
    # 10.x needs conventional-changelog-writer 9, which semantic-release 25 does not bundle.
    assert "conventional-changelog-conventionalcommits@9.3.1" in packages


def test_npm_publishing_configs_can_receive_a_token() -> None:
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    secrets = (data.get("on") or data.get(True))["workflow_call"]["secrets"]

    assert secrets["NPM_TOKEN"]["required"] is False
    assert _release_step()["env"]["NPM_TOKEN"] == "${{ secrets.NPM_TOKEN }}"
