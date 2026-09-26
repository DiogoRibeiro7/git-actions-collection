from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/workflow-lint.yml"
STEP = "Lint extra workflow files"
INPUT = "inputs.extra-workflow-files"
posix_only = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    for relative in (
        "examples/app/.github/workflows/ci.yml",
        "examples/mono/infra/.github/workflows/lint.yml",
        "examples/app/README.md",
    ):
        (repo / relative).parent.mkdir(parents=True, exist_ok=True)
        (repo / relative).write_text("on: push\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    untracked = repo / "examples/draft/.github/workflows/wip.yml"
    untracked.parent.mkdir(parents=True)
    untracked.write_text("on: push\n", encoding="utf-8")
    return repo


def _lint_extra(tmp_path: Path, pathspecs: str):
    repo = _repo(tmp_path)
    fakebin = make_fakebin(tmp_path / "tools", {"actionlint": 'echo "actionlint $*"'})
    return run_workflow_step(
        WORKFLOW,
        "lint",
        STEP,
        context={INPUT: pathspecs},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=repo,
    )


def test_extra_workflow_files_is_an_optional_input() -> None:
    data = _load(WORKFLOW)
    # YAML 1.1 reads the `on:` key as True.
    inputs = (data.get("on") or data[True])["workflow_call"]["inputs"]

    assert inputs["extra-workflow-files"]["required"] is False
    assert inputs["extra-workflow-files"]["default"] == ""


def test_extra_files_are_linted_only_when_listed_and_even_after_a_failure() -> None:
    steps = _load(WORKFLOW)["jobs"]["lint"]["steps"]
    step = next(step for step in steps if step.get("name") == STEP)

    assert step["if"] == "${{ !cancelled() && inputs.extra-workflow-files != '' }}"


def test_collection_ci_lints_every_example_workflow_with_the_pinned_tools() -> None:
    call = _load(ROOT / ".github/workflows/ci-tests.yml")["jobs"]["workflow-lint"]
    pathspecs = call["with"]["extra-workflow-files"].split()

    assert call["uses"] == "./.github/workflows/workflow-lint.yml"
    assert pathspecs == [
        "examples/**/.github/workflows/*.yml",
        "examples/**/.github/workflows/*.yaml",
    ]
    assert "actionlint" not in (ROOT / ".github/workflows/examples-smoke.yml").read_text(
        encoding="utf-8"
    )


@posix_only
def test_extra_pathspecs_select_tracked_workflow_files(tmp_path: Path) -> None:
    result = _lint_extra(tmp_path, "  examples/**/.github/workflows/*.yml\n\n")

    assert result.code == 0, result.stderr
    assert result.stdout.splitlines() == [
        "Linting 2 extra workflow files.",
        "actionlint -pyflakes= examples/app/.github/workflows/ci.yml "
        "examples/mono/infra/.github/workflows/lint.yml",
    ]


@posix_only
def test_pathspecs_that_match_nothing_fail(tmp_path: Path) -> None:
    result = _lint_extra(tmp_path, "templates/*.yml\n")

    assert result.code == 1
    assert "::error::extra-workflow-files matched no tracked files: templates/*.yml" in (
        result.stdout
    )
    assert "actionlint -pyflakes" not in result.stdout


@posix_only
def test_blank_pathspecs_lint_nothing_else(tmp_path: Path) -> None:
    result = _lint_extra(tmp_path, "  \n\n")

    assert result.code == 0, result.stderr
    assert result.stdout.splitlines() == [
        "extra-workflow-files lists no pathspecs; nothing else to lint."
    ]
