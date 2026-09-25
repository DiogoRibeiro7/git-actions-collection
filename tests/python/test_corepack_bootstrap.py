"""Node.js 25 and newer no longer bundle Corepack, so each `corepack enable` installs it first."""

import os
from pathlib import Path
import re

import pytest

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

ROOT = Path(__file__).resolve().parents[2]
INSTALL = re.compile(r"npm install --global corepack@(\S+)")


def test_every_corepack_enable_installs_one_pinned_corepack() -> None:
    paths = [*ROOT.glob(".github/workflows/*.yml"), *ROOT.glob("scripts/**/*.sh")]
    sites = sorted(path for path in paths if "corepack enable" in path.read_text(encoding="utf-8"))
    versions: dict[str, list[str]] = {}

    for path in sites:
        text = path.read_text(encoding="utf-8")
        name = path.relative_to(ROOT).as_posix()
        for enable in re.finditer("corepack enable", text):
            installs = INSTALL.findall(text[: enable.start()])
            assert installs, f"{name}: corepack enable without installing Corepack on Node.js 25+"
            versions.setdefault(installs[-1], []).append(name)

    assert sites
    assert len(versions) == 1, f"Corepack pinned to several versions: {versions}"


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
@pytest.mark.parametrize(("node_major", "installs"), [("24", False), ("26", True)])
def test_node_ci_installs_corepack_only_when_node_lacks_it(
    tmp_path: Path, node_major: str, installs: bool
) -> None:
    fakebin = make_fakebin(
        tmp_path,
        {
            "node": f"echo {node_major}",
            "npm": 'echo "npm $*"',
            "corepack": 'echo "corepack $*"',
        },
    )

    result = run_workflow_step(
        ".github/workflows/node-ci.yml",
        "build",
        "Enable Corepack",
        context={},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    expected = ["npm install --global corepack@0.36.0"] if installs else []
    assert result.stdout.splitlines() == [*expected, "corepack enable"]
