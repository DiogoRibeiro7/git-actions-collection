"""Repository-level regression tests for public identity and hygiene."""

from __future__ import annotations

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_REPOSITORY = "github.com/DiogoRibeiro7/git-actions-collection"
STALE_REPOSITORY = "github.com/DiogoRibeiro7/gh-actions-collection"


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


def test_public_metadata_uses_canonical_repository_url() -> None:
    """Prevent public documentation from drifting back to the old repository slug."""
    for relative_path in ("README.md", "pyproject.toml"):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert STALE_REPOSITORY not in text, f"stale repository URL in {relative_path}"
        assert CANONICAL_REPOSITORY in text, f"canonical repository URL missing from {relative_path}"


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
