"""setup-node's `cache: yarn` runs the global Yarn 1's `yarn cache dir`, which exits 1 in
projects that pin Yarn 2+ through packageManager, so node-ci failed before installing."""

import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/node-ci.yml"


def _steps() -> list[dict[str, Any]]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["build"]["steps"]


def test_yarn_is_cached_after_corepack_not_by_setup_node() -> None:
    steps = _steps()
    names = [step.get("name") for step in steps]
    setup_node = next(s for s in steps if s.get("uses", "").startswith("actions/setup-node@"))

    assert "cache" not in setup_node["with"]
    assert names.index("Enable Corepack") < names.index("Locate the Yarn cache") < names.index(
        "Cache Yarn packages"
    ) < names.index("Install dependencies")


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
@pytest.mark.parametrize(
    ("version", "expected"),
    [("1.22.22", "yarn cache dir"), ("4.1.1", "yarn config get cacheFolder")],
)
def test_the_projects_own_yarn_names_the_cache(tmp_path: Path, version: str, expected: str) -> None:
    fakebin = make_fakebin(
        tmp_path,
        {"yarn": f'if [ "$1" = "--version" ]; then echo {version}; else echo "yarn $*"; fi'},
    )

    result = run_workflow_step(
        WORKFLOW,
        "build",
        "Locate the Yarn cache",
        context={},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.outputs["dir"] == expected
