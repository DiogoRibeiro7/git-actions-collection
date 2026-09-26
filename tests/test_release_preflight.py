from __future__ import annotations

from pathlib import Path
import subprocess

import pytest
import yaml

from scripts.interface_snapshot import SNAPSHOT, current_interfaces, render
from scripts.release_preflight import (
    changelog_errors,
    previous_release,
    stale_branch_references,
    validate_release,
)

RELEASE_WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/repository-release.yml"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _write_release_metadata(root: Path, version: str) -> None:
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "demo"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## {version} - 2026-09-26\n\n### Added\n\n- A change.\n",
        encoding="utf-8",
    )


def _repo(root: Path, version: str) -> Path:
    """A git repository ready to release ``version`` with nothing supported yet."""
    _git(root, "init", "-q")
    _write_release_metadata(root, version)
    (root / ".github").mkdir()
    (root / ".github" / "support-matrix.yml").write_text(
        yaml.safe_dump({"composite_actions": {"supported": []}, "workflows": {"supported": {}}}),
        encoding="utf-8",
    )
    return root


def _support_workflow(root: Path, inputs: dict[str, dict[str, object]]) -> None:
    """Make wf.yml the only supported component and record its snapshot."""
    workflows = root / ".github" / "workflows"
    workflows.mkdir(exist_ok=True)
    (workflows / "wf.yml").write_text(
        yaml.safe_dump(
            {
                "on": {"workflow_call": {"inputs": inputs}},
                "permissions": {"contents": "read"},
                "jobs": {"run": {"runs-on": "ubuntu-latest"}},
            }
        ),
        encoding="utf-8",
    )
    (root / ".github" / "support-matrix.yml").write_text(
        yaml.safe_dump(
            {
                "composite_actions": {"supported": []},
                "workflows": {"supported": {"wf.yml": {"evidence": []}}},
            }
        ),
        encoding="utf-8",
    )
    (root / SNAPSHOT).write_text(render(current_interfaces(root)), encoding="utf-8")


def _tag(root: Path, tag: str) -> None:
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", tag)
    _git(root, "tag", tag)


def _level(default: str) -> dict[str, dict[str, object]]:
    return {"level": {"type": "string", "default": default, "description": "Level"}}


def _released_repo(root: Path) -> Path:
    """A repository that released v1.0.0 and is preparing 1.1.0."""
    _repo(root, "1.0.0")
    _support_workflow(root, _level("1"))
    _tag(root, "v1.0.0")
    _write_release_metadata(root, "1.1.0")
    return root


def _validate(root: Path, version: str, **kwargs: bool) -> list[str]:
    return validate_release(
        root=root, version=version, default_branch="main", prerelease=False, paths=[], **kwargs
    )


def test_stable_release_requires_main_and_matching_metadata(tmp_path: Path) -> None:
    _repo(tmp_path, "1.0.0")
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
    _repo(tmp_path, "1.0.0")
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
    _repo(tmp_path, "0.9.0")
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
    _repo(tmp_path, "0.9.0")
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
    _repo(tmp_path, "1.0.0")
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
    _repo(tmp_path, "1.0.0")
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


def test_stable_release_needs_a_dated_changelog_section(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## 1.0.0 - 2026-09-26\n", encoding="utf-8")

    assert changelog_errors(tmp_path, "1.0.0") == []
    assert changelog_errors(tmp_path, "1.1.0") == [
        "CHANGELOG.md has no '## 1.1.0 - YYYY-MM-DD' section"
    ]

    changelog.write_text("# Changelog\n\n## 1.1.0\n\n## 1.0.0 - 2026-09-26\n", encoding="utf-8")
    assert changelog_errors(tmp_path, "1.1.0") == [
        "CHANGELOG.md has no '## 1.1.0 - YYYY-MM-DD' section"
    ]


def test_stable_release_must_not_leave_entries_unreleased(tmp_path: Path) -> None:
    _repo(tmp_path, "1.0.0")
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## Unreleased\n\n- Later.\n\n" + changelog.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    assert _validate(tmp_path, "1.0.0") == [
        "CHANGELOG.md still has an Unreleased section; move its entries into the release section"
    ]


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("1.3.0", "v1.2.0"),
        ("1.11.0", "v1.10.0"),
        ("2.1.0-rc.1", "v2.0.0"),
        ("1.2.1", "v1.2.0"),
        ("1.0.0", None),
    ],
)
def test_previous_release_is_the_newest_older_stable_tag(version: str, expected: str) -> None:
    tags = ["v1", "v1.0.0", "v1.2.0", "v1.3.0-rc.1", "v1.10.0", "v2.0.0", "latest"]

    assert previous_release(tags, version) == expected


def test_preflight_requires_the_interface_snapshot_to_be_current(tmp_path: Path) -> None:
    _repo(tmp_path, "1.0.0")
    _support_workflow(tmp_path, _level("1"))
    (tmp_path / SNAPSHOT).unlink()

    assert _validate(tmp_path, "1.0.0") == [
        ".github/supported-interfaces.json does not match the supported workflows and "
        "actions; run python scripts/interface_snapshot.py --check"
    ]


def test_compatible_changes_since_the_previous_release_pass(tmp_path: Path) -> None:
    repo = _released_repo(tmp_path)
    _support_workflow(
        repo, {**_level("1"), "extra": {"type": "boolean", "default": False, "description": "x"}}
    )

    assert _validate(repo, "1.1.0") == []


def test_breaking_changes_since_the_previous_release_fail(tmp_path: Path) -> None:
    repo = _released_repo(tmp_path)
    _support_workflow(repo, _level("2"))

    errors = _validate(repo, "1.1.0")

    assert errors[0] == (
        "breaking change since v1.0.0: wf.yml: input 'level' default changed from '1' to '2'"
    )
    assert "--allow-breaking-changes" in errors[1]
    assert len(errors) == 2


def test_releaser_can_accept_breaking_changes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _released_repo(tmp_path)
    _support_workflow(repo, _level("2"))

    assert _validate(repo, "1.1.0", allow_breaking=True) == []
    assert "Accepted breaking change since v1.0.0: wf.yml: input 'level' default changed" in (
        capsys.readouterr().out
    )


def test_a_new_major_version_may_break_compatibility(tmp_path: Path) -> None:
    repo = _released_repo(tmp_path)
    _support_workflow(repo, _level("2"))
    _write_release_metadata(repo, "2.0.0")

    assert _validate(repo, "2.0.0") == []


def test_releases_before_the_snapshot_existed_are_not_compared(tmp_path: Path) -> None:
    repo = _repo(tmp_path, "1.0.0")
    _tag(repo, "v1.0.0")
    _support_workflow(repo, _level("2"))
    _write_release_metadata(repo, "1.1.0")

    assert _validate(repo, "1.1.0") == []


def test_repository_release_validates_before_anything_can_write() -> None:
    workflow = yaml.safe_load(RELEASE_WORKFLOW.read_text(encoding="utf-8"))
    preflight, release = workflow["jobs"]["preflight"], workflow["jobs"]["release"]
    preflight_run = next(
        step["run"] for step in preflight["steps"] if step.get("name") == "Run release preflight"
    )

    assert workflow["permissions"] == {"contents": "read"}
    assert "permissions" not in preflight
    assert preflight["steps"][0]["with"]["persist-credentials"] is False
    assert "-m scripts.release_preflight" in preflight_run
    assert "--allow-breaking-changes" in preflight_run
    assert release["needs"] == "preflight"
    assert release["permissions"] == {"contents": "write"}
    assert release["steps"][0]["with"]["ref"] == "${{ needs.preflight.outputs.commit }}"


def test_repository_release_configures_tag_identity() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert 'git config user.name "github-actions[bot]"' in workflow
    assert (
        'git config user.email "41898282+github-actions[bot]@users.noreply.github.com"'
        in workflow
    )
    assert workflow.index("Configure release tag identity") < workflow.index("Create version tag")
