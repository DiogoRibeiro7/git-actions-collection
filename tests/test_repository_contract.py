"""Repository-level regression tests for public identity and hygiene."""

from __future__ import annotations

from pathlib import Path
import subprocess

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


def test_migrated_consumer_surfaces_have_no_stale_repository_slug() -> None:
    """Keep the consumer surfaces migrated in PR #76 on the canonical repository."""
    paths = [
        "examples/*/README.md",
        "scripts/pypi_trusted_publishing_wizard.py",
    ]
    completed = subprocess.run(
        ["git", "grep", "-n", "-F", STALE_SLUG, "--", *paths],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1, completed.stdout


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
