"""Helm publishing lives in its own workflow.

helm-chart-lint-test.yml offered publishing but capped its token at contents: read,
so it could never push. Granting writes there would make every read-only caller
fail at startup, even callers that never publish.
"""

import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / ".github/workflows/helm-chart-release.yml"
LINT = ROOT / ".github/workflows/helm-chart-lint-test.yml"
posix_only = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")


def _load(path: Path) -> dict[Any, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_release_is_a_dry_run_unless_asked_and_pushes_from_an_environment() -> None:
    data = _load(RELEASE)
    inputs = (data.get("on") or data.get(True))["workflow_call"]["inputs"]
    package, publish = data["jobs"]["package"], data["jobs"]["publish"]

    assert inputs["dry-run"]["default"] is True
    assert package["permissions"] == {"contents": "read"}
    assert publish["needs"] == "package"
    assert publish["if"] == "${{ !inputs.dry-run }}"
    assert publish["environment"] == "${{ inputs.release-environment }}"
    assert publish["permissions"] == {"contents": "read", "packages": "write"}


@posix_only
def test_package_step_reports_the_chart_file(tmp_path: Path) -> None:
    fakebin = make_fakebin(
        tmp_path,
        {"helm": 'dest="${@: -1}"; touch "$dest/demo-0.1.0.tgz"; echo "helm $*"'},
    )
    runner_temp = tmp_path / "runner-temp"
    runner_temp.mkdir()

    result = run_workflow_step(
        RELEASE,
        "package",
        "Package chart",
        context={"inputs.chart-path": "charts/demo"},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}", "RUNNER_TEMP": str(runner_temp)},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert f"helm package charts/demo --destination {runner_temp}/chart" in result.stdout
    assert result.outputs["chart"] == "demo-0.1.0.tgz"


@posix_only
@pytest.mark.parametrize(
    ("repository", "registry", "target"),
    [
        ("", "ghcr.io", "oci://ghcr.io/myorg/charts"),
        ("oci://registry.example.com/team/charts", "registry.example.com",
         "oci://registry.example.com/team/charts"),
    ],
)
def test_push_logs_in_without_exposing_the_password(
    tmp_path: Path, repository: str, registry: str, target: str
) -> None:
    fakebin = make_fakebin(
        tmp_path, {"helm": 'echo "helm $*"; if [ "$2" = login ]; then echo "stdin=$(cat)"; fi'}
    )

    result = run_workflow_step(
        RELEASE,
        "publish",
        "Push chart",
        context={
            "inputs.oci-repository": repository,
            "github.repository_owner": "MyOrg",
            "needs.package.outputs.chart": "demo-0.1.0.tgz",
            "secrets.REGISTRY_USERNAME || github.actor": "bot",
            "secrets.REGISTRY_PASSWORD || github.token": "s3cret",
        },
        env={"PATH": f"{fakebin}:{os.environ['PATH']}", "RUNNER_TEMP": "/rt"},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    assert result.stdout.splitlines() == [
        f"helm registry login {registry} --username bot --password-stdin",
        "stdin=s3cret",
        f"helm push /rt/chart/demo-0.1.0.tgz {target}",
    ]


def test_lint_workflow_pins_helm_and_no_longer_publishes() -> None:
    steps = {step.get("name"): step for step in _load(LINT)["jobs"]["lint"]["steps"]}

    assert steps["Set up Helm"]["with"]["version"] == "v4.3.0"
    assert steps["Reject publishing"]["if"] == "${{ inputs.publish }}"
    assert all("helm push" not in step.get("run", "") for step in steps.values())
    assert "--dry-run" not in steps["Helm template"]["run"]


@posix_only
def test_asking_the_lint_workflow_to_publish_fails_with_directions(tmp_path: Path) -> None:
    result = run_workflow_step(LINT, "lint", "Reject publishing", context={}, workdir=tmp_path)

    assert result.code == 1
    assert "Call helm-chart-release.yml with dry-run: false" in result.stdout
