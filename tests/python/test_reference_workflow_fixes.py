"""Regression tests for a batch of reference and experimental workflow fixes."""

import json
import os
from pathlib import Path
import subprocess
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github/workflows"
posix_only = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
ZERO = "0" * 40


def _load(name: str) -> dict[Any, Any]:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def _inputs(name: str) -> dict[str, Any]:
    data = _load(name)
    return (data.get("on") or data.get(True))["workflow_call"]["inputs"]


def _steps(name: str, job: str) -> dict[str, dict[str, Any]]:
    return {step.get("name") or step.get("uses"): step for step in _load(name)["jobs"][job]["steps"]}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def _commit(repo: Path, message: str, *paths: str) -> str:
    for path in paths:
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(f"{path} {message}", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--allow-empty", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def test_api_testing_does_not_require_a_lockfile() -> None:
    setup = next(
        step for job in _load("api-testing.yml")["jobs"].values() for step in job.get("steps", [])
        if step.get("uses", "").startswith("actions/setup-node@")
    )

    assert "cache" not in setup["with"]


def test_concurrency_template_does_not_share_its_callers_group() -> None:
    group = _load("concurrency-caching.yml")["concurrency"]["group"]

    assert group.startswith("concurrency-caching-")


def test_artifact_cleanup_asks_for_a_package_name() -> None:
    description = _inputs("artifact-management.yml")["package-name"]["description"]

    assert "without registry or owner" in description


def test_default_toolchains_are_supported_releases() -> None:
    assert json.loads(_inputs("ruby-ci.yml")["ruby-versions"]["default"]) == ["3.3", "3.4"]
    assert _inputs("go-ci.yml")["go-version"]["default"] == "1.27"
    lint = next(
        step for job in _load("go-ci.yml")["jobs"].values() for step in job["steps"]
        if step.get("uses", "").startswith("golangci/golangci-lint-action@")
    )
    assert lint["with"]["version"] == "v2.14.0"


def test_dotnet_cache_needs_a_lock_file() -> None:
    setup = next(
        step for job in _load("dotnet-ci.yml")["jobs"].values() for step in job["steps"]
        if step.get("uses", "").startswith("actions/setup-dotnet@")
    )

    assert setup["with"]["cache"] == "${{ hashFiles('**/packages.lock.json') != '' }}"


def test_kubeconform_is_pinned_and_checksummed() -> None:
    install = _steps("k8s-manifests-lint.yml", "lint")["Install kubeconform"]

    assert install["env"]["VERSION"] == "v0.8.0"
    assert "sha256sum --check" in install["run"]
    assert "/usr/local/bin" not in install["run"]


@posix_only
def test_kubeconform_skips_schemaless_resources_and_github_files(tmp_path: Path) -> None:
    fakebin = make_fakebin(tmp_path, {"kubeconform": 'printf "kubeconform"; printf " [%s]" "$@"; echo'})

    result = run_workflow_step(
        WORKFLOWS / "k8s-manifests-lint.yml",
        "lint",
        "Validate manifests",
        context={"inputs.paths": "deploy charts"},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.stdout.strip() == (
        "kubeconform [-summary] [-ignore-missing-schemas] [-ignore-filename-pattern] "
        "[(^|/)[.]github/] [deploy] [charts]"
    )


@posix_only
@pytest.mark.parametrize(
    ("before", "config_file", "expected"),
    [
        ("base", None, ["--from", "<base>", "--to", "HEAD", "--extends", "@commitlint/config-conventional"]),
        (ZERO, None, ["--last", "--extends", "@commitlint/config-conventional"]),
        ("base", "commitlint.config.js", ["--from", "<base>", "--to", "HEAD"]),
    ],
)
def test_commitlint_checks_every_pushed_commit(
    tmp_path: Path, before: str, config_file: str | None, expected: list[str]
) -> None:
    """Only HEAD's subject was checked before, so earlier commits in a push slipped through."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    base = _commit(repo, "chore: base")
    _commit(repo, "bad commit message")
    _commit(repo, "feat: good")
    if config_file:
        (repo / config_file).write_text("module.exports = {}\n", encoding="utf-8")
    fakebin = make_fakebin(tmp_path / "tools", {"npx": 'printf "%s\\n" "$@"'})

    result = run_workflow_step(
        WORKFLOWS / "conventional-commits.yml",
        "lint",
        "Conventional commits check (push)",
        context={"github.event.before": base if before == "base" else before},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}"},
        workdir=repo,
    )

    assert result.code == 0, result.stderr
    args = result.stdout.splitlines()
    assert args[args.index("commitlint") + 1:] == [base if a == "<base>" else a for a in expected]


@posix_only
@pytest.mark.parametrize(
    ("scenario", "changed"),
    [("earlier-commit", "true"), ("untouched", "false"), ("no-base", "true")],
)
def test_lambda_changes_are_detected_across_the_whole_push(
    tmp_path: Path, scenario: str, changed: str
) -> None:
    """Comparing with HEAD^ missed a function changed in an earlier commit of the push."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    base = _commit(repo, "base", "functions/api/app.py", "functions/web/app.py")
    if scenario == "earlier-commit":
        _commit(repo, "change api", "functions/api/app.py")
    _commit(repo, "change web", "functions/web/app.py")
    _git(repo, "remote", "add", "origin", str(repo))

    result = run_workflow_step(
        WORKFLOWS / "aws-lambda-deploy.yml",
        "deploy",
        "Detect changes",
        context={
            "matrix.function.path": "functions/api",
            "github.event.pull_request.base.sha || github.event.before": ZERO
            if scenario == "no-base" else base,
        },
        workdir=repo,
    )

    assert result.code == 0, result.stderr
    assert result.outputs["changed"] == changed
