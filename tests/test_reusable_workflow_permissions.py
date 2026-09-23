"""Guard the permission ceiling GitHub enforces on local reusable-workflow calls.

GitHub validates every nested job's permissions against the calling job before
evaluating any ``if:`` condition. A caller that grants less than a nested job
requests fails with ``startup_failure`` and no jobs, so the run never appears
as a pull-request check and the gap goes unnoticed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
LOCAL_PREFIX = "./.github/workflows/"
LEVELS = {"none": 0, "read": 1, "write": 2}
LEVEL_NAMES = {value: name for name, value in LEVELS.items()}


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _level(permissions: Any, scope: str) -> int:
    """Return the access level a permissions block grants for one scope."""
    if permissions == "write-all":
        return LEVELS["write"]
    if permissions == "read-all":
        return LEVELS["none"] if scope == "id-token" else LEVELS["read"]
    if isinstance(permissions, dict):
        return LEVELS[permissions.get(scope, "none")]
    raise AssertionError(f"unsupported permissions block: {permissions!r}")


def _escalations(path: Path, ceiling: Any, chain: tuple[str, ...]) -> list[str]:
    """Find jobs in a called workflow that request more than ``ceiling`` allows."""
    document = _load(path)
    problems: list[str] = []

    for job_id, job in document.get("jobs", {}).items():
        location = (*chain, f"{path.name}:{job_id}")
        requested = job.get("permissions", document.get("permissions"))

        if isinstance(requested, dict):
            for scope in sorted(requested):
                wanted, allowed = _level(requested, scope), _level(ceiling, scope)
                if wanted > allowed:
                    problems.append(
                        f"{' -> '.join(location)} requests {scope}: {LEVEL_NAMES[wanted]} "
                        f"but the caller only allows {LEVEL_NAMES[allowed]}"
                    )

        uses = job.get("uses")
        if isinstance(uses, str) and uses.startswith(LOCAL_PREFIX):
            nested_ceiling = ceiling if requested is None else requested
            problems.extend(_escalations(ROOT / uses, nested_ceiling, location))

    return problems


def test_local_reusable_workflow_callers_grant_nested_permissions() -> None:
    problems: list[str] = []

    for path in sorted(WORKFLOWS.glob("*.yml")):
        document = _load(path)
        for job_id, job in document.get("jobs", {}).items():
            uses = job.get("uses")
            if not (isinstance(uses, str) and uses.startswith(LOCAL_PREFIX)):
                continue

            ceiling = job.get("permissions", document.get("permissions"))
            if ceiling is None:
                # Undeclared permissions inherit repository defaults, which
                # cannot be known statically.
                continue

            problems.extend(_escalations(ROOT / uses, ceiling, (f"{path.name}:{job_id}",)))

    assert not problems, (
        "Callers must grant every permission a nested job requests, even when "
        "that job is skipped by an if: condition:\n" + "\n".join(problems)
    )


def test_escalation_check_flags_skipped_mutating_jobs(tmp_path: Path) -> None:
    """The guard must flag the shape that previously caused silent startup failures."""
    called = tmp_path / "called.yml"
    called.write_text(
        yaml.safe_dump(
            {
                "permissions": {"contents": "read"},
                "jobs": {
                    "dry-run": {"permissions": {"contents": "read"}},
                    "publish": {
                        "if": "${{ !inputs.dry-run }}",
                        "permissions": {"contents": "read", "id-token": "write"},
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    read_only = _escalations(called, {"contents": "read"}, ("caller.yml:smoke",))
    granted = _escalations(called, {"contents": "read", "id-token": "write"}, ("caller.yml:smoke",))

    assert read_only == [
        "caller.yml:smoke -> called.yml:publish requests id-token: write "
        "but the caller only allows none"
    ]
    assert granted == []
