from __future__ import annotations

from pathlib import Path

from scripts.release_preflight import stale_branch_references, validate_release


def _write_pyproject(root: Path, version: str) -> None:
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "demo"\nversion = "{version}"\n',
        encoding="utf-8",
    )


def test_stable_release_requires_main_and_matching_metadata(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "1.0.0")
    clean = tmp_path / "README.md"
    clean.write_text("uses: owner/repo/action@v1\n", encoding="utf-8")

    assert validate_release(
        root=tmp_path,
        version="1.0.0",
        default_branch="main",
        prerelease=False,
        paths=[clean],
    ) == []


def test_preflight_rejects_wrong_default_branch(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "1.0.0")
    clean = tmp_path / "README.md"
    clean.write_text("clean\n", encoding="utf-8")

    errors = validate_release(
        root=tmp_path,
        version="1.0.0",
        default_branch="develop",
        prerelease=False,
        paths=[clean],
    )

    assert any("default branch must be main" in error for error in errors)


def test_preflight_rejects_stable_version_mismatch(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "0.9.0")
    clean = tmp_path / "README.md"
    clean.write_text("clean\n", encoding="utf-8")

    errors = validate_release(
        root=tmp_path,
        version="1.0.0",
        default_branch="main",
        prerelease=False,
        paths=[clean],
    )

    assert any("does not match stable release" in error for error in errors)


def test_prerelease_does_not_require_pyproject_version_match(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "0.9.0")
    clean = tmp_path / "README.md"
    clean.write_text("clean\n", encoding="utf-8")

    assert validate_release(
        root=tmp_path,
        version="1.0.0-rc.1",
        default_branch="main",
        prerelease=True,
        paths=[clean],
    ) == []


def test_preflight_rejects_retired_branch_references(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "1.0.0")
    stale = tmp_path / "workflow.yml"
    stale.write_text("uses: owner/repo/action@" + "develop" + "\n", encoding="utf-8")

    errors = validate_release(
        root=tmp_path,
        version="1.0.0",
        default_branch="main",
        prerelease=False,
        paths=[stale],
    )

    assert any("retired develop-branch references" in error for error in errors)
    assert stale_branch_references([stale]) == [str(stale)]


def test_preflight_rejects_invalid_version(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "1.0.0")
    clean = tmp_path / "README.md"
    clean.write_text("clean\n", encoding="utf-8")

    errors = validate_release(
        root=tmp_path,
        version="v1",
        default_branch="main",
        prerelease=False,
        paths=[clean],
    )

    assert any("semantic version" in error for error in errors)
