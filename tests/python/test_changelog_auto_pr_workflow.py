from pathlib import Path
from typing import Any

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/changelog-auto-pr.yml"


def _load() -> dict[Any, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_git_cliff_comes_from_a_pinned_release_not_apt() -> None:
    """Ubuntu has no git-cliff package, so `apt-get install git-cliff` failed every run."""
    steps = {step.get("name"): step for step in _load()["jobs"]["generate"]["steps"]}
    install = steps["Install git-cliff"]

    assert install["uses"].startswith("taiki-e/install-action@")
    assert install["with"]["tool"].startswith("git-cliff@")
    assert all("apt-get" not in step.get("run", "") for step in steps.values())


def test_inputs_are_described() -> None:
    data = _load()
    inputs = (data.get("on") or data.get(True))["workflow_call"]["inputs"]

    assert all(spec.get("description") for spec in inputs.values())
