import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.action_refs import is_commit_pinned
from tests.utils.fake_runner import ActionResult, run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(".github/workflows/rust-github-release.yml")
BUILD_SHA = "a" * 40


def _load_workflow() -> dict[str, Any]:
    """Load the reusable Rust GitHub Release workflow."""
    path = Path(".github/workflows/rust-github-release.yml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _workflow_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Return workflow_call inputs while handling YAML's reserved 'on' token."""
    on_block = data.get("on") or data.get(True)
    return on_block["workflow_call"]["inputs"]


def test_rust_github_release_defaults_are_non_mutating() -> None:
    """Release creation must require an explicit live opt-in."""
    inputs = _workflow_inputs(_load_workflow())

    assert inputs["rust-toolchain"]["default"] == "stable"
    assert inputs["working-directory"]["default"] == "."
    assert inputs["package-name"]["default"] == ""
    assert inputs["locked"]["default"] is False
    assert inputs["tag-prefix"]["default"] == "v"
    assert inputs["tag-name"]["default"] == ""
    assert inputs["release-title"]["default"] == ""
    assert inputs["prerelease"]["default"] is False
    assert inputs["draft"]["default"] is False
    assert inputs["generate-notes"]["default"] is True
    assert inputs["dry-run"]["default"] is True
    assert inputs["release-environment"]["default"] == "release"
    assert inputs["artifact-retention-days"]["default"] == 7


def test_rust_github_release_reuses_verified_preflight() -> None:
    """GitHub Release assets should come from the existing release preflight."""
    data = _load_workflow()
    preflight = data["jobs"]["preflight"]

    assert preflight["uses"] == "./.github/workflows/rust-release-preflight.yml"
    assert preflight["with"]["upload-crate"] is True
    assert preflight["with"]["package-name"] == "${{ inputs.package-name }}"


def test_rust_github_release_generates_and_verifies_sha256() -> None:
    """Prepared release assets should include a checked SHA256SUMS file."""
    data = _load_workflow()
    steps = data["jobs"]["assets"]["steps"]
    steps_by_name = {step.get("name"): step for step in steps if step.get("name")}

    generate = steps_by_name["Generate SHA-256 checksums"]["run"]
    verify = steps_by_name["Verify checksum file"]["run"]

    assert "sha256sum ./*.crate > SHA256SUMS" in generate
    assert "sha256sum --check SHA256SUMS" in verify


def test_rust_github_release_uses_pinned_artifact_actions() -> None:
    """Artifact movement must use immutable action SHAs."""
    data = _load_workflow()
    rendered = Path(".github/workflows/rust-github-release.yml").read_text(
        encoding="utf-8"
    )
    uses = [
        step["uses"]
        for job in data["jobs"].values()
        for step in job.get("steps", [])
        if "uses" in step
    ]

    assert any(is_commit_pinned(ref, "actions/download-artifact") for ref in uses)
    assert any(is_commit_pinned(ref, "actions/upload-artifact") for ref in uses)
    # An untagged download-artifact commit this workflow was once pinned to.
    assert "484a0b528fb4d7bd804637ccb632e47a0e638317" not in rendered


def test_rust_github_release_requires_version_tag_match() -> None:
    """Release tags should identify the Cargo package version exactly."""
    data = _load_workflow()
    steps = data["jobs"]["assets"]["steps"]
    resolve = next(step for step in steps if step.get("name") == "Resolve release identity")

    assert 'expected_tag="${TAG_PREFIX}${PACKAGE_VERSION}"' in resolve["run"]
    assert "tag-name must match Cargo package version" in resolve["run"]


def test_rust_github_release_live_job_is_protected() -> None:
    """The mutating job should be opt-in, environment-protected, and write-scoped."""
    data = _load_workflow()
    job = data["jobs"]["release"]

    assert job["if"] == "${{ !inputs.dry-run }}"
    assert job["environment"] == "${{ inputs.release-environment }}"
    assert job["permissions"] == {"contents": "write"}


def test_rust_github_release_blocks_unsafe_events() -> None:
    """Live release creation should only accept manual dispatch or matching tag pushes."""
    data = _load_workflow()
    steps = data["jobs"]["release"]["steps"]
    validate = next(
        step for step in steps if step.get("name") == "Validate live release context"
    )

    assert "workflow_dispatch" in validate["run"]
    assert '"refs/tags/$TAG_NAME"' in validate["run"]
    assert "Live GitHub Release creation is blocked for event" in validate["run"]


def test_rust_github_release_uses_generated_notes_and_verified_tag() -> None:
    """GitHub CLI should require an existing tag and optionally generate notes."""
    data = _load_workflow()
    steps = data["jobs"]["release"]["steps"]
    create = next(step for step in steps if step.get("name") == "Create GitHub Release")

    assert "--verify-tag" in create["run"]
    assert "args+=(--generate-notes)" in create["run"]
    assert "release-assets/*" in create["run"]


def test_rust_github_release_has_executable_dry_run_self_test() -> None:
    """Exercise packaging and checksums without creating a GitHub Release."""
    path = Path(".github/workflows/test-rust-github-release.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["rust-github-release-dry-run"]
    assert smoke["uses"] == "./.github/workflows/rust-github-release.yml"
    # The skipped release job's grant must be allowed or the run fails at startup.
    assert smoke["permissions"] == {"contents": "write"}
    assert smoke["with"] == {
        "rust-toolchain": "stable",
        "working-directory": "examples/rust-crate",
        "package-name": "rust-crate",
        "tag-name": "v0.1.0",
        "dry-run": True,
        "artifact-retention-days": 1,
    }


def test_rust_github_release_gh_steps_target_the_caller_repository() -> None:
    """The release job has no checkout, so gh must be told which repository to use."""
    steps = _load_workflow()["jobs"]["release"]["steps"]
    gh_steps = [step for step in steps if "gh " in str(step.get("run", ""))]

    assert {step["name"] for step in gh_steps} == {
        "Validate live release context",
        "Create GitHub Release",
    }
    for step in gh_steps:
        assert step["env"]["GH_REPO"] == "${{ github.repository }}"
        assert step["env"]["GH_TOKEN"] == "${{ github.token }}"


# Behaves like the real CLI for the calls the release job makes, including the
# "not a git repository" failure when GH_REPO is missing and no checkout exists.
GH_STUB = r"""
printf '%s\n' "$*" >> "$GH_STUB_LOG"
if [ -z "${GH_REPO:-}" ]; then
  echo "failed to run git: fatal: not a git repository (or any of the parent directories): .git" >&2
  exit 1
fi
case "$1 $2" in
  "api repos/"*)
    if [ -z "${GH_STUB_TAG_SHA:-}" ]; then
      echo "gh: No commit found for SHA: $2 (HTTP 422)" >&2
      exit 1
    fi
    echo "$GH_STUB_TAG_SHA"
    ;;
  "release view")
    case "${GH_STUB_RELEASE:-missing}" in
      missing) echo "release not found" >&2; exit 1 ;;
      exists) echo "https://github.com/$GH_REPO/releases/tag/$3" ;;
      *) echo "$GH_STUB_RELEASE" >&2; exit 1 ;;
    esac
    ;;
  "release create")
    echo "https://github.com/$GH_REPO/releases/tag/$3"
    ;;
  *)
    echo "unexpected gh call: $*" >&2
    exit 2
    ;;
esac
"""

posix_only = pytest.mark.skipif(os.name != "posix", reason="Fake runner requires bash (Linux CI)")


def _release_context(**overrides: str) -> dict[str, str]:
    """Expression values for the live release job, overridable per test."""
    context = {
        "github.token": "stub-token",
        "github.repository": "owner/repo",
        "github.event_name": "push",
        "github.ref": "refs/tags/v1.2.3",
        "github.sha": BUILD_SHA,
        "needs.assets.outputs.tag-name": "v1.2.3",
        "inputs.release-environment": "release",
        "inputs.release-title": "",
        "inputs.generate-notes": "true",
        "inputs.prerelease": "false",
        "inputs.draft": "false",
    }
    context.update(overrides)
    return context


def _run_release_step(
    tmp_path: Path, step_name: str, context: dict[str, str], **stub: str
) -> tuple[ActionResult, list[str]]:
    """Run a live release step against the gh stub and return its recorded calls."""
    log = tmp_path / "gh.log"
    fakebin = make_fakebin(tmp_path, {"gh": GH_STUB})
    env = {"PATH": f"{fakebin}:{os.environ['PATH']}", "GH_STUB_LOG": str(log), **stub}
    result = run_workflow_step(WORKFLOW, "release", step_name, context, env=env, workdir=tmp_path)
    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    return result, calls


def _prepare_release_assets(tmp_path: Path) -> None:
    assets = tmp_path / "release-assets"
    assets.mkdir()
    (assets / "demo-1.2.3.crate").write_bytes(b"crate")
    (assets / "SHA256SUMS").write_text("checksum  ./demo-1.2.3.crate\n", encoding="utf-8")


@posix_only
@pytest.mark.parametrize(
    ("event", "ref"),
    [("push", "refs/tags/v1.2.3"), ("workflow_dispatch", "refs/heads/main")],
)
def test_live_release_accepts_tag_on_built_commit(tmp_path: Path, event: str, ref: str) -> None:
    """A tag push, or a dispatch from the tagged commit, may create the release."""
    context = _release_context(**{"github.event_name": event, "github.ref": ref})
    result, calls = _run_release_step(
        tmp_path, "Validate live release context", context, GH_STUB_TAG_SHA=BUILD_SHA
    )

    assert result.code == 0, result.stderr
    assert calls == ["api repos/owner/repo/commits/refs/tags/v1.2.3 --jq .sha"]


@posix_only
@pytest.mark.parametrize(
    ("overrides", "tag_sha", "message"),
    [
        (
            {"github.event_name": "workflow_dispatch", "github.ref": "refs/heads/main"},
            "b" * 40,
            f"Tag v1.2.3 points to {'b' * 40}, but the release assets were built from {BUILD_SHA}",
        ),
        ({}, "", "Release tag v1.2.3 does not exist or could not be resolved"),
        ({"github.ref": "refs/tags/v9.9.9"}, BUILD_SHA, "from push requires refs/tags/v1.2.3"),
        ({"github.event_name": "pull_request"}, BUILD_SHA, "blocked for event: pull_request"),
        ({"github.event_name": "release"}, BUILD_SHA, "blocked for event: release"),
        ({"inputs.release-environment": ""}, BUILD_SHA, "release-environment must not be empty"),
    ],
)
def test_live_release_rejects_unsafe_context(
    tmp_path: Path, overrides: dict[str, str], tag_sha: str, message: str
) -> None:
    """Wrong events, refs, missing tags, and tags on other commits must stop the release."""
    result, _ = _run_release_step(
        tmp_path,
        "Validate live release context",
        _release_context(**overrides),
        GH_STUB_TAG_SHA=tag_sha,
    )

    assert result.code != 0
    assert message in result.stderr


@posix_only
def test_live_release_creates_release_from_verified_tag(tmp_path: Path) -> None:
    """A missing release is created for the existing tag with both assets attached."""
    _prepare_release_assets(tmp_path)
    result, calls = _run_release_step(tmp_path, "Create GitHub Release", _release_context())

    assert result.code == 0, result.stderr
    assert calls[0] == "release view v1.2.3 --json url --jq .url"
    create = calls[1].split()
    assert create[:3] == ["release", "create", "v1.2.3"]
    assert "release-assets/demo-1.2.3.crate" in create
    assert "release-assets/SHA256SUMS" in create
    assert calls[1].endswith("--verify-tag --title v1.2.3 --generate-notes")


@posix_only
def test_live_release_applies_optional_release_flags(tmp_path: Path) -> None:
    """Title, prerelease, draft, and notes options reach gh release create."""
    _prepare_release_assets(tmp_path)
    context = _release_context(
        **{
            "inputs.release-title": "Demo 1.2.3",
            "inputs.generate-notes": "false",
            "inputs.prerelease": "true",
            "inputs.draft": "true",
        }
    )
    result, calls = _run_release_step(tmp_path, "Create GitHub Release", context)

    assert result.code == 0, result.stderr
    assert calls[1].endswith("--verify-tag --title Demo 1.2.3 --prerelease --draft")


@posix_only
@pytest.mark.parametrize(
    ("lookup", "message"),
    [
        ("exists", "GitHub Release already exists for v1.2.3"),
        ("HTTP 401: Bad credentials", "Could not check for an existing GitHub Release"),
    ],
)
def test_live_release_never_overwrites_or_guesses(tmp_path: Path, lookup: str, message: str) -> None:
    """Existing releases and inconclusive lookups must both stop before creation."""
    _prepare_release_assets(tmp_path)
    result, calls = _run_release_step(
        tmp_path, "Create GitHub Release", _release_context(), GH_STUB_RELEASE=lookup
    )

    assert result.code != 0
    assert message in result.stderr
    assert not any(call.startswith("release create") for call in calls)
