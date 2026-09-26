import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/docker-build-push.yml"
SAME_BUILD = ("context", "file", "build-args", "target")


def _steps() -> dict[str, dict[str, Any]]:
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["build"]["steps"]
    return {step.get("name"): step for step in steps}


def test_the_scan_gates_the_push() -> None:
    steps = _steps()
    names = list(steps)

    assert names.index("Build image for vulnerability scan") < names.index(
        "Scan image for vulnerabilities"
    ) < names.index("Build and push")
    candidate = steps["Build image for vulnerability scan"]["with"]
    scan = steps["Scan image for vulnerabilities"]["with"]
    assert candidate["load"] is True and candidate["push"] is False
    assert scan["image-ref"] == candidate["tags"]
    assert scan["exit-code"] == "1"
    assert steps["Build and push"]["with"]["push"] is True
    assert "if" not in steps["Build and push"]  # it only runs once the scan has passed


def test_the_scanned_image_is_built_like_the_pushed_one() -> None:
    steps = _steps()
    candidate = steps["Build image for vulnerability scan"]["with"]
    pushed = steps["Build and push"]["with"]

    assert {key: candidate[key] for key in SAME_BUILD} == {key: pushed[key] for key in SAME_BUILD}
    assert candidate["platforms"] == "${{ steps.scan-platform.outputs.value }}"
    assert candidate["cache-from"] == pushed["cache-from"]


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
@pytest.mark.parametrize(
    ("platforms", "expected"),
    [
        ("linux/amd64", "linux/amd64"),
        (" linux/arm64 , linux/amd64", "linux/arm64"),
        ("\nlinux/amd64\nlinux/arm64\n", "linux/amd64"),
    ],
)
def test_the_first_platform_is_scanned(tmp_path: Path, platforms: str, expected: str) -> None:
    result = run_workflow_step(
        WORKFLOW,
        "build",
        "Select platform for vulnerability scan",
        context={"inputs.platforms": platforms},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.outputs["value"] == expected


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
def test_image_names_are_lowercased_for_the_registry(tmp_path: Path) -> None:
    """github.repository keeps the owner's case, which registries reject."""
    result = run_workflow_step(
        WORKFLOW,
        "build",
        "Normalize image tags",
        context={"inputs.image": "ghcr.io/MyOrg/My-App", "inputs.tags": "v1.2.0, latest"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.outputs["value"].splitlines() == [
        "ghcr.io/myorg/my-app:v1.2.0",
        "ghcr.io/myorg/my-app:latest",
    ]


@pytest.mark.parametrize("alias", ["publish-docker-on-tag.yml", "release-container.yml"])
def test_aliases_move_latest_only_for_release_tags(alias: str) -> None:
    data = yaml.safe_load((ROOT / ".github/workflows" / alias).read_text(encoding="utf-8"))

    assert data["jobs"]["publish"]["with"]["tags"] == (
        "${{ github.ref_type == 'tag' && format('{0},latest', github.ref_name) || github.sha }}"
    )


def test_release_container_has_no_placeholder_build_settings() -> None:
    data = yaml.safe_load(
        (ROOT / ".github/workflows/release-container.yml").read_text(encoding="utf-8")
    )
    build = data["jobs"]["publish"]["with"]

    assert build["target"] == "${{ inputs.target }}"
    assert build["build-args"] == "${{ inputs.build-args }}"
