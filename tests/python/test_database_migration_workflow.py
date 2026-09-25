import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/database-migration.yml"


def _load() -> dict[Any, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _steps() -> dict[str, dict[str, Any]]:
    return {step.get("name"): step for step in _load()["jobs"]["migrate"]["steps"]}


def test_dry_run_previews_sql_and_skips_the_migration() -> None:
    steps = _steps()

    assert steps["Dry run"]["if"] == "inputs.dry-run == true"
    assert steps["Apply migrations"]["if"] == "${{ !inputs.dry-run }}"
    # The rollback only follows a migration that ran and failed.
    assert steps["Rollback"]["if"] == "failure() && steps.migrate.outcome == 'failure'"


def test_tool_installs_stay_together_on_the_path() -> None:
    """Flyway and Liquibase launchers load their libraries from their own directory."""
    steps = _steps()

    for name in ("Setup Flyway", "Setup Liquibase"):
        run = steps[name]["run"]
        assert "/usr/local/bin" not in run
        assert 'tar xz -C "$RUNNER_TEMP' in run
        assert '>> "$GITHUB_PATH"' in run


@pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
@pytest.mark.parametrize(
    ("step", "extracted_into", "on_path"),
    [
        ("Setup Flyway", "", "/flyway-9.22.3"),  # the archive has a top-level directory
        ("Setup Liquibase", "/liquibase", "/liquibase"),  # the archive does not
    ],
)
def test_setup_steps_add_the_install_directory_to_the_path(
    tmp_path: Path, step: str, extracted_into: str, on_path: str
) -> None:
    fakebin = make_fakebin(tmp_path, {"curl": "true", "tar": 'echo "tar $*"'})
    github_path = tmp_path / "github_path"

    result = run_workflow_step(
        WORKFLOW,
        "migrate",
        step,
        context={},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}", "GITHUB_PATH": str(github_path)},
        workdir=tmp_path,
    )

    assert result.code == 0, result.stderr
    [added] = github_path.read_text(encoding="utf-8").splitlines()
    assert added.endswith(on_path)
    runner_temp = added[: -len(on_path)]
    assert result.stdout.splitlines() == [f"tar xz -C {runner_temp}{extracted_into}"]


def test_flyway_license_key_can_come_from_inherited_secrets() -> None:
    data = _load()
    secrets = (data.get("on") or data.get(True))["workflow_call"]["secrets"]

    assert secrets["FLYWAY_LICENSE_KEY"]["required"] is False
    assert secrets["flyway-license-key"]["description"].startswith("Deprecated:")
    assert data["jobs"]["migrate"]["env"]["FLYWAY_LICENSE_KEY"] == (
        "${{ secrets.FLYWAY_LICENSE_KEY || secrets.flyway-license-key }}"
    )


def test_callers_pass_per_environment_secrets_with_inherit() -> None:
    """Per-environment secret names cannot be declared, and undeclared secrets are rejected."""
    example = yaml.safe_load(
        (ROOT / "examples/database-migration/.github/workflows/migrate.yml").read_text(encoding="utf-8")
    )
    guide = (ROOT / "docs/database-migration.md").read_text(encoding="utf-8")

    assert example["jobs"]["migrate"]["secrets"] == "inherit"
    assert "secrets: inherit" in guide
    assert "DEV_DATABASE_URL: ${{" not in guide
