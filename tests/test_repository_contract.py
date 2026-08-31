"""Repository-level regression tests for public identity and hygiene."""

from __future__ import annotations

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SLUG = "DiogoRibeiro7/git-actions-collection"
CANONICAL_REPOSITORY_URL = f"github.com/{CANONICAL_SLUG}"
STALE_SLUG = "DiogoRibeiro7/" + "gh-actions-collection"
LEGACY_REFERENCE_ALLOWLIST = ROOT / "tests" / "fixtures" / "legacy_repository_reference_paths.txt"


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


def _stale_reference_paths() -> set[str]:
    """Return tracked paths that still contain the legacy repository slug."""
    completed = subprocess.run(
        [
            "git",
            "grep",
            "-l",
            "-F",
            STALE_SLUG,
            "--",
            ".",
            ":!tests/test_repository_contract.py",
            ":!tests/fixtures/legacy_repository_reference_paths.txt",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode in {0, 1}, completed.stderr
    return {line.strip() for line in completed.stdout.splitlines() if line.strip()}


def test_public_metadata_uses_canonical_repository_identity() -> None:
    """Keep the public slug and package metadata aligned with the real repository."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert STALE_SLUG not in readme
    assert STALE_SLUG not in pyproject
    assert CANONICAL_SLUG in readme
    assert CANONICAL_REPOSITORY_URL in pyproject


def test_legacy_repository_reference_debt_is_explicit() -> None:
    """Forbid new stale references and require the migration debt manifest to stay exact."""
    allowed = {
        line.strip()
        for line in LEGACY_REFERENCE_ALLOWLIST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    actual = _stale_reference_paths()

    unexpected = actual - allowed
    resolved_but_allowlisted = allowed - actual

    assert not unexpected, f"untracked legacy repository references: {sorted(unexpected)}"
    assert not resolved_but_allowlisted, (
        "remove migrated paths from legacy reference allowlist: "
        f"{sorted(resolved_but_allowlisted)}"
    )


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
