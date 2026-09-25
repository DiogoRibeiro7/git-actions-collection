from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/pytorch-train-deploy.yml"


def _load() -> dict[Any, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _inputs() -> dict[str, Any]:
    data = _load()
    return (data.get("on") or data.get(True))["workflow_call"]["inputs"]


def test_gpu_access_is_opt_in() -> None:
    """ubuntu-latest has no GPU, and Docker refuses to start a container with --gpus there."""
    job = _load()["jobs"]["train"]
    inputs = _inputs()

    assert inputs["gpu"] == {
        "description": inputs["gpu"]["description"],
        "type": "boolean",
        "default": False,
    }
    assert job["container"]["options"] == "${{ inputs.gpu && '--gpus all' || '' }}"


def test_runner_is_configurable_for_gpu_runners() -> None:
    assert _inputs()["runs-on"]["default"] == "ubuntu-latest"
    assert _load()["jobs"]["train"]["runs-on"] == "${{ inputs.runs-on }}"


def test_workflow_requests_only_read_access() -> None:
    assert _load()["permissions"] == {"contents": "read"}


def test_every_input_is_described() -> None:
    assert all(spec.get("description") for spec in _inputs().values())
