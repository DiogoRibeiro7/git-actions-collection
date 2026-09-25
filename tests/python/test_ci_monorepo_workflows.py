import json
import os
from pathlib import Path
import subprocess

import pytest

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / ".github/workflows/ci-monorepo-matrix.yml"
RUNNER = ROOT / ".github/workflows/ci-monorepo-runner.yml"
BASE = "github.event.pull_request.base.sha || github.event.before"
pytestmark = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit_everywhere(repo: Path, *paths: str) -> str:
    for path in paths:
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(path, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "change")
    return _git(repo, "rev-parse", "HEAD")


def test_changes_in_several_folders_become_one_matrix(tmp_path: Path) -> None:
    """A multi-line step output without a delimiter made the detect job fail."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    base = _commit_everywhere(repo, "README.md")
    head = _commit_everywhere(repo, "api/app.py", "web/index.js", "docs/guide.md")

    changed = run_workflow_step(
        MATRIX,
        "detect",
        "Determine changed top-level paths",
        context={BASE: base, "github.sha": head},
        workdir=repo,
    )
    assert changed.code == 0, changed.stderr
    assert changed.outputs["changed_paths"].split() == ["api", "docs", "web"]

    matrix = run_workflow_step(
        MATRIX,
        "detect",
        "Build matrix",
        context={
            "inputs.groups": json.dumps({"api": "python", "web": "node"}),
            "steps.changed.outputs.changed_paths": changed.outputs["changed_paths"],
        },
        workdir=repo,
    )
    assert matrix.code == 0, matrix.stderr
    assert json.loads(matrix.outputs["matrix"]) == {
        "include": [
            {"top": "api", "kind": "python", "path": "api"},
            {"top": "web", "kind": "node", "path": "web"},
        ]
    }
    assert matrix.outputs["count"] == "2"


def test_nested_workflows_are_linted_from_the_working_directory(tmp_path: Path) -> None:
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/ci.yml").write_text("on: push\n", encoding="utf-8")
    fakebin = make_fakebin(tmp_path, {"actionlint": 'echo "actionlint $*"'})

    result = run_workflow_step(
        RUNNER,
        "run-kind",
        "Lint workflows (if present)",
        context={},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.stdout.splitlines() == ["actionlint .github/workflows/ci.yml"]


def test_invalid_kubernetes_manifests_fail(tmp_path: Path) -> None:
    (tmp_path / "deploy.yaml").write_text("kind: Deployment\n", encoding="utf-8")
    fakebin = make_fakebin(tmp_path, {"kubeconform": 'echo "kubeconform $*"; exit 1'})

    result = run_workflow_step(
        RUNNER,
        "run-kind",
        "Kubernetes manifests lint",
        context={},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )

    assert result.code == 1
    assert "kubeconform -summary -ignore-missing-schemas ./deploy.yaml" in result.stdout


def test_terraform_is_validated_after_init(tmp_path: Path) -> None:
    fakebin = make_fakebin(tmp_path, {"terraform": 'echo "terraform $*"'})

    result = run_workflow_step(
        RUNNER,
        "run-kind",
        "Terraform init",
        context={},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.stdout.splitlines() == [
        "terraform -version",
        "terraform init -backend=false",
        "terraform validate",
    ]
