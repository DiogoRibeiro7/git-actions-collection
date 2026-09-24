from __future__ import annotations

from collections.abc import Callable
import copy
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts import interface_snapshot as snapshot

ROOT = Path(__file__).resolve().parents[1]


def test_supported_interfaces_match_the_snapshot() -> None:
    """Every change to a supported interface must be recorded deliberately."""
    recorded = json.loads((ROOT / snapshot.SNAPSHOT).read_text(encoding="utf-8"))
    current = snapshot.current_interfaces(ROOT)
    breaking, additive = snapshot.compare(recorded, current)

    assert not breaking and not additive, (
        "Supported interfaces differ from .github/supported-interfaces.json.\n"
        "Compatible changes: run `python scripts/interface_snapshot.py --write`.\n"
        "Breaking changes are not allowed within a major version; see SUPPORT.md.\n"
        + "\n".join(
            [
                *(f"breaking: {line}" for line in breaking),
                *(f"compatible: {line}" for line in additive),
            ]
        )
    )
    assert recorded == current


def test_snapshot_is_rendered_canonically() -> None:
    text = (ROOT / snapshot.SNAPSHOT).read_text(encoding="utf-8").replace("\r\n", "\n")

    assert text == snapshot.render(json.loads(text))


BASE: dict[str, Any] = {
    "composite_actions": {
        "act": {
            "inputs": {"name": {"required": True, "default": None, "deprecated": False}},
            "outputs": ["report"],
        }
    },
    "workflows": {
        "wf.yml": {
            "inputs": {
                "level": {"type": "string", "required": False, "default": "1", "deprecated": False}
            },
            "outputs": ["url"],
            "secrets": {"token": {"required": False}},
            "permissions": {"contents": "read"},
        }
    },
}


def _diff(mutate: Callable[[dict[str, Any]], object]) -> tuple[list[str], list[str]]:
    current = copy.deepcopy(BASE)
    mutate(current)
    return snapshot.compare(BASE, current)


def _wf(interface: dict[str, Any]) -> dict[str, Any]:
    return interface["workflows"]["wf.yml"]


def test_identical_interfaces_have_no_differences() -> None:
    assert snapshot.compare(BASE, copy.deepcopy(BASE)) == ([], [])


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda c: _wf(c)["inputs"].pop("level"), "wf.yml: input 'level' was removed"),
        (
            lambda c: _wf(c)["inputs"]["level"].update(type="number"),
            "input 'level' changed type from 'string' to 'number'",
        ),
        (
            lambda c: _wf(c)["inputs"]["level"].update(required=True),
            "input 'level' became required",
        ),
        (
            lambda c: _wf(c)["inputs"]["level"].update(default="2"),
            "input 'level' default changed from '1' to '2'",
        ),
        (
            lambda c: _wf(c)["inputs"].update(
                extra={"type": "string", "required": True, "default": None, "deprecated": False}
            ),
            "required input 'extra' was added",
        ),
        (lambda c: _wf(c)["outputs"].remove("url"), "output 'url' was removed"),
        (lambda c: _wf(c)["secrets"].pop("token"), "secret 'token' was removed"),
        (
            lambda c: _wf(c)["secrets"]["token"].update(required=True),
            "secret 'token' became required",
        ),
        (
            lambda c: _wf(c)["secrets"].update(key={"required": True}),
            "required secret 'key' was added",
        ),
        (
            lambda c: _wf(c)["permissions"].update(contents="write"),
            "callers must now grant contents: write (was read)",
        ),
        (
            lambda c: _wf(c)["permissions"].update({"id-token": "write"}),
            "callers must now grant id-token: write (was none)",
        ),
        (lambda c: c["composite_actions"].pop("act"), "act: is no longer supported"),
        (
            lambda c: c["composite_actions"]["act"]["outputs"].clear(),
            "act: output 'report' was removed",
        ),
    ],
)
def test_breaking_changes_are_classified(
    mutate: Callable[[dict[str, Any]], object], message: str
) -> None:
    breaking, additive = _diff(mutate)

    assert any(message in line for line in breaking), breaking
    assert additive == []


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda c: _wf(c)["inputs"].update(
                extra={"type": "string", "required": False, "default": "", "deprecated": False}
            ),
            "optional input 'extra' was added",
        ),
        (lambda c: _wf(c)["outputs"].append("sha"), "output 'sha' was added"),
        (
            lambda c: _wf(c)["secrets"].update(key={"required": False}),
            "optional secret 'key' was added",
        ),
        (
            lambda c: _wf(c)["inputs"]["level"].update(deprecated=True),
            "input 'level' is now deprecated",
        ),
        (
            lambda c: _wf(c)["permissions"].pop("contents"),
            "callers no longer need contents: read (now none)",
        ),
        (
            lambda c: c["composite_actions"]["act"]["inputs"]["name"].update(required=False),
            "input 'name' became optional",
        ),
        (
            lambda c: c["composite_actions"].update(new={"inputs": {}, "outputs": []}),
            "new: is newly supported",
        ),
    ],
)
def test_compatible_changes_are_classified(
    mutate: Callable[[dict[str, Any]], object], message: str
) -> None:
    breaking, additive = _diff(mutate)

    assert breaking == []
    assert any(message in line for line in additive), additive


def test_caller_permissions_include_nested_and_conditional_jobs(tmp_path: Path) -> None:
    """GitHub checks skipped and nested jobs too, so callers must grant their permissions."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "inner.yml").write_text(
        yaml.safe_dump(
            {
                "permissions": {"contents": "read"},
                "jobs": {"publish": {"if": "false", "permissions": {"id-token": "write"}}},
            }
        ),
        encoding="utf-8",
    )
    outer = {
        "permissions": {"contents": "read"},
        "jobs": {
            "build": {},
            "nested": {"uses": "./.github/workflows/inner.yml"},
            "release": {"if": "false", "permissions": {"contents": "write"}},
        },
    }

    assert snapshot.caller_permissions(tmp_path, outer) == {
        "contents": "write",
        "id-token": "write",
    }
    assert snapshot.caller_permissions(
        tmp_path, {"permissions": "read-all", "jobs": {"a": {}}}
    ) == {"*": "read"}


def _fixture_repo(root: Path, description: str = "Level") -> Path:
    action = root / ".github" / "actions" / "act"
    action.mkdir(parents=True)
    (action / "action.yml").write_text(
        yaml.safe_dump(
            {
                "inputs": {"mode": {"description": "Mode", "default": "fast"}},
                "outputs": {"report": {"value": "x"}},
                "runs": {"using": "composite", "steps": []},
            }
        ),
        encoding="utf-8",
    )
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    _write_workflow(root, {"level": {"type": "string", "default": "1", "description": description}})
    (root / ".github" / "support-matrix.yml").write_text(
        yaml.safe_dump(
            {
                "composite_actions": {"supported": ["act"]},
                "workflows": {"supported": {"wf.yml": {"evidence": []}}},
            }
        ),
        encoding="utf-8",
    )
    return root


def _write_workflow(root: Path, inputs: dict[str, Any]) -> None:
    (root / ".github" / "workflows" / "wf.yml").write_text(
        yaml.safe_dump(
            {
                "on": {"workflow_call": {"inputs": inputs}},
                "permissions": {"contents": "read"},
                "jobs": {"run": {"runs-on": "ubuntu-latest"}},
            }
        ),
        encoding="utf-8",
    )


def test_deprecated_inputs_are_detected_from_their_description(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path, description="Deprecated: use `levels` instead.")

    interface = snapshot.current_interfaces(repo)

    assert interface["workflows"]["wf.yml"]["inputs"]["level"]["deprecated"] is True
    assert interface["composite_actions"]["act"]["inputs"]["mode"]["deprecated"] is False


def test_write_then_check_round_trips(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _fixture_repo(tmp_path)

    assert snapshot.main(["--root", str(repo), "--write"]) == 0
    assert snapshot.main(["--root", str(repo), "--check"]) == 0
    assert "Supported interfaces match the snapshot." in capsys.readouterr().out


def test_check_reports_breaking_and_compatible_changes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _fixture_repo(tmp_path)
    snapshot.main(["--root", str(repo), "--write"])
    _write_workflow(repo, {"levels": {"type": "string", "default": "", "description": "Levels"}})
    capsys.readouterr()

    assert snapshot.main(["--root", str(repo), "--check"]) == 1

    out = capsys.readouterr().out
    assert "Breaking changes" in out
    assert "wf.yml: input 'level' was removed" in out
    assert "Compatible changes (record them with --write)" in out
    assert "wf.yml: optional input 'levels' was added" in out


def test_check_without_a_snapshot_lists_every_supported_component(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _fixture_repo(tmp_path)

    assert snapshot.main(["--root", str(repo), "--check"]) == 1
    out = capsys.readouterr().out
    assert "act: is newly supported" in out
    assert "wf.yml: is newly supported" in out
