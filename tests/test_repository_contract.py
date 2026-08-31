"""Repository-level regression tests for public identity and hygiene."""

from __future__ import annotations

from pathlib import Path
import re
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


def test_tracked_content_has_no_stale_repository_slug() -> None:
    """Prevent the retired repository identity from re-entering tracked content."""
    completed = subprocess.run(
        ["git", "grep", "-n", "-F", STALE_SLUG, "--", "."],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1, completed.stdout


def test_collection_consumer_refs_do_not_use_stale_main() -> None:
    """Keep collection self-references off main until main is the supported stable surface."""
    pattern = re.compile(rf"{re.escape(CANONICAL_SLUG)}/.+@main\b")
    offenders: list[str] = []
    for relative in sorted(_tracked_paths()):
        path = ROOT / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if pattern.search(text):
            offenders.append(relative)
    assert not offenders, f"canonical collection references still use @main: {offenders}"


def test_pypi_wizard_uses_current_pre_v1_consumer_ref() -> None:
    """Keep generated PyPI workflows on the current pre-v1 integration ref."""
    wizard = (ROOT / "scripts" / "pypi_trusted_publishing_wizard.py").read_text(encoding="utf-8")
    expected = (
        "uses: DiogoRibeiro7/git-actions-collection/"
        ".github/workflows/publish-to-pypi.yml@develop"
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
