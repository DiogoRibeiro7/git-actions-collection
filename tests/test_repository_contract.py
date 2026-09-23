"""Repository-level regression tests for public identity and hygiene."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

import yaml

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SLUG = "DiogoRibeiro7/git-actions-collection"
CANONICAL_REPOSITORY_URL = f"github.com/{CANONICAL_SLUG}"
STALE_SLUG = "DiogoRibeiro7/" + "gh-actions-collection"


def _tracked_paths() -> set[str]:
    """Return paths tracked by Git in the current checkout."""
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in completed.stdout.splitlines() if line.strip()}


def test_public_metadata_uses_canonical_repository_identity() -> None:
    """Keep the public slug and package metadata aligned with the real repository."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert STALE_SLUG not in readme
    assert STALE_SLUG not in pyproject
    assert CANONICAL_SLUG in readme
    assert CANONICAL_REPOSITORY_URL in pyproject


def test_tracked_content_has_no_stale_repository_slug() -> None:
    """Prevent the retired repository identity from re-entering tracked content."""
    completed = subprocess.run(
        ["git", "grep", "-n", "-F", STALE_SLUG, "--", "."],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1, completed.stdout


def test_composite_actions_resolve_bundled_helpers_from_action_path() -> None:
    """Prevent exported actions from assuming collection helpers exist in the caller workspace."""
    offenders: list[str] = []
    for action_file in sorted((ROOT / ".github" / "actions").glob("*/action.yml")):
        data = yaml.safe_load(action_file.read_text(encoding="utf-8"))
        for step in data.get("runs", {}).get("steps", []):
            command = str(step.get("run") or "")
            uses = str(step.get("uses") or "")
            if "bash scripts/" in command or command.startswith("scripts/"):
                offenders.append(f"{action_file.relative_to(ROOT)}: {command}")
            if uses.startswith("./.github/actions/"):
                offenders.append(f"{action_file.relative_to(ROOT)}: uses {uses}")
    assert not offenders, f"composite actions contain caller-relative bundled helpers: {offenders}"


def test_pypi_wizard_uses_canonical_publish_workflow() -> None:
    """Keep generated PyPI workflows on the canonical publishing workflow."""
    wizard = (ROOT / "scripts" / "pypi_trusted_publishing_wizard.py").read_text(encoding="utf-8")
    expected = (
        "uses: DiogoRibeiro7/git-actions-collection/"
        ".github/workflows/pypi-publish.yml@v1"
    )
    assert expected in wizard


def test_generated_outputs_are_not_tracked() -> None:
    """Keep local coverage and compiled build products out of the repository."""
    tracked = _tracked_paths()
    offenders = {
        path
        for path in tracked
        if path == "coverage.xml"
        or Path(path).name == ".coverage"
        or Path(path).name.startswith(".coverage.")
        or path.startswith("htmlcov/")
        or "/target/" in f"/{path}"
    }
    assert not offenders, f"generated artefacts are tracked: {sorted(offenders)}"


def test_gitignore_covers_generated_outputs() -> None:
    """Ensure common local test/build outputs remain ignored."""
    ignored = set((ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
    required = {"coverage.xml", ".coverage", ".coverage.*", "htmlcov/", "target/"}
    assert required <= ignored


def test_legacy_publish_workflows_remain_thin_compatibility_aliases() -> None:
    """Prevent legacy publishing entry points from growing separate implementations."""
    aliases = {
        "publish-to-pypi.yml": "./.github/workflows/pypi-publish.yml",
        "publish-to-npm.yml": "./.github/workflows/npm-publish.yml",
        "publish-docker-on-tag.yml": "./.github/workflows/docker-build-push.yml",
        "release-container.yml": "./.github/workflows/docker-build-push.yml",
    }

    for filename, target in aliases.items():
        path = ROOT / ".github" / "workflows" / filename
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        jobs = data["jobs"]
        assert len(jobs) == 1
        job = next(iter(jobs.values()))
        assert job["uses"] == target
        assert "steps" not in job
