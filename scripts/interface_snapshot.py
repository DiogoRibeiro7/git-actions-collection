#!/usr/bin/env python3
"""Record and check the public interface of supported workflows and actions.

`.github/supported-interfaces.json` is the machine-readable compatibility record
for the supported tier. Any interface change must update it in the same pull
request; `--check` reports each difference as additive or breaking so reviewers
can apply the deprecation policy in SUPPORT.md.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
from typing import Any

import yaml

SNAPSHOT = Path(".github/supported-interfaces.json")
SUPPORT_MATRIX = Path(".github/support-matrix.yml")
LOCAL_WORKFLOW_PREFIX = "./.github/workflows/"
LEVELS = {"none": 0, "read": 1, "write": 2}

Interface = dict[str, Any]


def _load_yaml(path: Path) -> dict[Any, Any]:
    # Keys are not only strings: YAML 1.1 parses the `on:` trigger key as True.
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _deprecated(spec: Mapping[str, Any]) -> bool:
    """Deprecated inputs say so at the start of their description."""
    return str(spec.get("description", "")).strip().lower().startswith("deprecated")


def _merge_permissions(result: dict[str, str], requested: Any) -> None:
    """Raise each scope in *result* to the level *requested* grants."""
    if isinstance(requested, str):
        requested = {"*": requested.removesuffix("-all")}
    if not isinstance(requested, Mapping):
        return
    for scope, level in requested.items():
        if LEVELS.get(level, 0) > LEVELS.get(result.get(scope, "none"), 0):
            result[scope] = level


def caller_permissions(root: Path, workflow: Mapping[str, Any]) -> dict[str, str]:
    """Return the permissions a caller must grant, including nested local workflows.

    GitHub validates every nested job against the caller before evaluating `if:`,
    so jobs that only run in some modes still count.
    """
    result: dict[str, str] = {}
    default = workflow.get("permissions")
    for job in (workflow.get("jobs") or {}).values():
        _merge_permissions(result, job.get("permissions", default))
        uses = job.get("uses")
        if isinstance(uses, str) and uses.startswith(LOCAL_WORKFLOW_PREFIX):
            nested = _load_yaml(root / uses)
            _merge_permissions(result, caller_permissions(root, nested))
    return dict(sorted(result.items()))


def workflow_interface(root: Path, name: str) -> Interface:
    """Describe a reusable workflow's `workflow_call` interface."""
    data = _load_yaml(root / ".github" / "workflows" / name)
    triggers = data.get("on") or data.get(True) or {}
    call = triggers.get("workflow_call") or {}
    return {
        "inputs": {
            key: {
                "type": spec.get("type"),
                "required": bool(spec.get("required", False)),
                "default": spec.get("default"),
                "deprecated": _deprecated(spec),
            }
            for key, spec in sorted((call.get("inputs") or {}).items())
        },
        "outputs": sorted(call.get("outputs") or {}),
        "secrets": {
            key: {"required": bool((spec or {}).get("required", False))}
            for key, spec in sorted((call.get("secrets") or {}).items())
        },
        "permissions": caller_permissions(root, data),
    }


def action_interface(root: Path, name: str) -> Interface:
    """Describe a composite action's inputs and outputs."""
    data = _load_yaml(root / ".github" / "actions" / name / "action.yml")
    return {
        "inputs": {
            key: {
                "required": bool(spec.get("required", False)),
                "default": spec.get("default"),
                "deprecated": _deprecated(spec),
            }
            for key, spec in sorted((data.get("inputs") or {}).items())
        },
        "outputs": sorted(data.get("outputs") or {}),
    }


def current_interfaces(root: Path) -> Interface:
    """Build the interface record for everything the support matrix marks supported."""
    matrix = _load_yaml(root / SUPPORT_MATRIX)
    return {
        "composite_actions": {
            name: action_interface(root, name)
            for name in sorted(matrix["composite_actions"]["supported"])
        },
        "workflows": {
            name: workflow_interface(root, name)
            for name in sorted(matrix["workflows"]["supported"])
        },
    }


def _compare_inputs(
    name: str, old: Mapping[str, Any], new: Mapping[str, Any], out: tuple[list[str], list[str]]
) -> None:
    breaking, additive = out
    for key in sorted(old.keys() - new.keys()):
        breaking.append(f"{name}: input {key!r} was removed")
    for key in sorted(new.keys() - old.keys()):
        if new[key]["required"]:
            breaking.append(f"{name}: required input {key!r} was added")
        else:
            additive.append(f"{name}: optional input {key!r} was added")
    for key in sorted(old.keys() & new.keys()):
        before, after = old[key], new[key]
        if before.get("type") != after.get("type"):
            breaking.append(
                f"{name}: input {key!r} changed type from {before.get('type')!r} "
                f"to {after.get('type')!r}"
            )
        if before["required"] != after["required"]:
            target = breaking if after["required"] else additive
            state = "required" if after["required"] else "optional"
            target.append(f"{name}: input {key!r} became {state}")
        if before.get("default") != after.get("default"):
            breaking.append(
                f"{name}: input {key!r} default changed from {before.get('default')!r} "
                f"to {after.get('default')!r}"
            )
        if before.get("deprecated") != after.get("deprecated"):
            state = "deprecated" if after.get("deprecated") else "no longer deprecated"
            additive.append(f"{name}: input {key!r} is now {state}")


def _compare_component(
    name: str, old: Interface, new: Interface, out: tuple[list[str], list[str]]
) -> None:
    breaking, additive = out
    _compare_inputs(name, old.get("inputs", {}), new.get("inputs", {}), out)

    old_outputs, new_outputs = set(old.get("outputs", [])), set(new.get("outputs", []))
    breaking.extend(
        f"{name}: output {key!r} was removed" for key in sorted(old_outputs - new_outputs)
    )
    additive.extend(
        f"{name}: output {key!r} was added" for key in sorted(new_outputs - old_outputs)
    )

    old_secrets, new_secrets = old.get("secrets", {}), new.get("secrets", {})
    for key in sorted(old_secrets.keys() - new_secrets.keys()):
        breaking.append(f"{name}: secret {key!r} was removed")
    for key in sorted(new_secrets.keys() - old_secrets.keys()):
        if new_secrets[key]["required"]:
            breaking.append(f"{name}: required secret {key!r} was added")
        else:
            additive.append(f"{name}: optional secret {key!r} was added")
    for key in sorted(old_secrets.keys() & new_secrets.keys()):
        if old_secrets[key]["required"] != new_secrets[key]["required"]:
            required = new_secrets[key]["required"]
            (breaking if required else additive).append(
                f"{name}: secret {key!r} became {'required' if required else 'optional'}"
            )

    old_permissions, new_permissions = old.get("permissions", {}), new.get("permissions", {})
    for scope in sorted(old_permissions.keys() | new_permissions.keys()):
        before = old_permissions.get(scope, "none")
        after = new_permissions.get(scope, "none")
        if LEVELS[after] > LEVELS[before]:
            breaking.append(f"{name}: callers must now grant {scope}: {after} (was {before})")
        elif LEVELS[after] < LEVELS[before]:
            additive.append(f"{name}: callers no longer need {scope}: {before} (now {after})")


def compare(recorded: Interface, current: Interface) -> tuple[list[str], list[str]]:
    """Classify every difference between two interface records."""
    out: tuple[list[str], list[str]] = ([], [])
    breaking, additive = out
    for kind in ("composite_actions", "workflows"):
        old_items, new_items = recorded.get(kind, {}), current.get(kind, {})
        for name in sorted(old_items.keys() - new_items.keys()):
            breaking.append(f"{name}: is no longer supported")
        for name in sorted(new_items.keys() - old_items.keys()):
            additive.append(f"{name}: is newly supported")
        for name in sorted(old_items.keys() & new_items.keys()):
            _compare_component(name, old_items[name], new_items[name], out)
    return breaking, additive


def render(interfaces: Interface) -> str:
    """Serialise deterministically so the snapshot diff is reviewable."""
    return json.dumps(interfaces, indent=2, sort_keys=True) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail when the snapshot is stale")
    mode.add_argument("--write", action="store_true", help="rewrite the snapshot")
    args = parser.parse_args(argv)

    snapshot = args.root / SNAPSHOT
    current = current_interfaces(args.root)
    if args.write:
        snapshot.write_text(render(current), encoding="utf-8")
        print(f"Wrote {SNAPSHOT}")
        return 0

    recorded = json.loads(snapshot.read_text(encoding="utf-8")) if snapshot.exists() else {}
    breaking, additive = compare(recorded, current)
    if not breaking and not additive:
        print("Supported interfaces match the snapshot.")
        return 0
    if breaking:
        print("Breaking changes (not allowed within a major version; deprecate instead):")
        print("\n".join(f"  - {line}" for line in breaking))
    if additive:
        print("Compatible changes (record them with --write):")
        print("\n".join(f"  - {line}" for line in additive))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
