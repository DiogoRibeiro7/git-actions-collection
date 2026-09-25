"""Render the documentation site's workflow reference pages and catalogue.

Every supported, reference and experimental workflow gets a page built from its
YAML: the description comment on its first lines, its support tier, a usage
snippet, and its inputs, outputs, secrets and the permissions a caller must
grant. The catalogue lists every public workflow and composite action by tier.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.action_docs import _cell, _default
from scripts.interface_snapshot import caller_permissions

REPOSITORY = "DiogoRibeiro7/git-actions-collection"
SUPPORT_MATRIX = Path(".github/support-matrix.yml")
WORKFLOWS = Path(".github/workflows")
ACTIONS = Path(".github/actions")
TIERS = ("supported", "reference", "experimental")
ADMONITIONS = {"supported": "success", "reference": "note", "experimental": "warning"}


@dataclass(frozen=True)
class Component:
    """A public workflow or composite action as the catalogue lists it."""

    kind: str  # "workflow" or "action"
    name: str  # workflow file name or action directory
    tier: str
    title: str
    description: str


def _load(path: Path) -> dict[Any, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def support_matrix(root: Path) -> dict[str, Any]:
    return _load(root / SUPPORT_MATRIX)


def workflow_description(path: Path) -> str:
    """Return the comment block that opens a workflow file."""
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            break
        lines.append(line.lstrip("#").strip())
    return " ".join(line for line in lines if line)


def public_components(root: Path) -> list[Component]:
    """List every supported, reference and experimental component in tier order."""
    matrix = support_matrix(root)
    components: list[Component] = []
    for tier in TIERS:
        for name in matrix["workflows"].get(tier) or []:
            path = root / WORKFLOWS / name
            title = str(_load(path).get("name") or name)
            components.append(Component("workflow", name, tier, title, workflow_description(path)))
        for name in matrix["composite_actions"].get(tier) or []:
            metadata = _load(root / ACTIONS / name / "action.yml")
            components.append(
                Component("action", name, tier, str(metadata.get("name") or name), str(metadata.get("description", "")))
            )
    return components


def _workflow_call(data: Mapping[Any, Any]) -> dict[str, Any]:
    triggers = data.get("on") or data.get(True) or {}
    return (triggers.get("workflow_call") or {}) if isinstance(triggers, dict) else {}


def _usage(component: Component, call: Mapping[str, Any], permissions: Mapping[str, str]) -> list[str]:
    job = component.name.rsplit(".", 1)[0]
    lines = [
        "```yaml",
        "jobs:",
        f"  {job}:",
        f"    uses: {REPOSITORY}/{WORKFLOWS.as_posix()}/{component.name}@v1",
    ]
    if permissions:
        lines.append("    permissions:")
        lines += [f"      {scope}: {level}" for scope, level in permissions.items()]
    required_inputs = {
        name: spec for name, spec in (call.get("inputs") or {}).items() if (spec or {}).get("required")
    }
    if required_inputs:
        lines.append("    with:")
        lines += [f"      {name}: <{(spec or {}).get('type', 'string')}>" for name, spec in required_inputs.items()]
    required_secrets = [name for name, spec in (call.get("secrets") or {}).items() if (spec or {}).get("required")]
    if required_secrets:
        lines.append("    secrets:")
        lines += [f"      {name}: ${{{{ secrets.{name} }}}}" for name in required_secrets]
    return [*lines, "```"]


def _yes(spec: Mapping[str, Any]) -> str:
    return "yes" if spec.get("required") else "no"


def render_workflow_page(
    root: Path,
    component: Component,
    definitions: Mapping[str, str],
    related: Iterable[tuple[str, str]] = (),
) -> str:
    """Render one workflow's reference page; relative links are from the repository root."""
    path = root / WORKFLOWS / component.name
    data = _load(path)
    call = _workflow_call(data)
    permissions = caller_permissions(root, data)
    inputs = call.get("inputs") or {}
    outputs = call.get("outputs") or {}
    secrets = call.get("secrets") or {}

    lines = [f"# {component.title}", ""]
    if component.description:
        lines += [component.description, ""]
    lines += [
        f'!!! {ADMONITIONS[component.tier]} "{component.tier.capitalize()}"',
        f"    {' '.join(str(definitions.get(component.tier, '')).split())}",
        "",
        "## Usage",
        "",
        *_usage(component, call, permissions),
        "",
    ]
    if permissions:
        lines.append("The calling job must grant at least these permissions; a reusable workflow cannot raise them.")
    else:
        lines.append("The workflow declares no permissions, so its jobs use the caller's token permissions.")
    lines += ["", "## Inputs", ""]
    if inputs:
        lines += ["| Input | Type | Required | Default | Description |", "| --- | --- | --- | --- | --- |"]
        lines += [
            f"| `{name}` | {(spec or {}).get('type', '')} | {_yes(spec or {})} | {_default(spec or {})} "
            f"| {_cell((spec or {}).get('description', ''))} |"
            for name, spec in inputs.items()
        ]
    else:
        lines.append("This workflow has no inputs.")
    if outputs:
        lines += ["", "## Outputs", "", "| Output | Description |", "| --- | --- |"]
        lines += [f"| `{name}` | {_cell((spec or {}).get('description', ''))} |" for name, spec in outputs.items()]
    if secrets:
        lines += ["", "## Secrets", "", "| Secret | Required | Description |", "| --- | --- | --- |"]
        lines += [
            f"| `{name}` | {_yes(spec or {})} | {_cell((spec or {}).get('description', ''))} |"
            for name, spec in secrets.items()
        ]
    related = list(related)
    if related:
        lines += ["", "## Guides and examples", ""]
        lines += [f"- [{title}]({link})" for title, link in related]
    source = f"{WORKFLOWS.as_posix()}/{component.name}"
    lines += ["", f"Source: [`{source}`](https://github.com/{REPOSITORY}/blob/main/{source})", ""]
    return "\n".join(lines)


def render_catalogue(
    components: Iterable[Component],
    definitions: Mapping[str, str],
    link: Callable[[Component], str],
) -> str:
    """Render the catalogue of public components, grouped by support tier."""
    components = list(components)
    lines = [
        "# Catalogue",
        "",
        "Every reusable workflow and composite action consumers can call, grouped by support tier.",
        "Call workflows and actions at `@v1` or at an exact commit SHA; see the",
        "[support policy](SUPPORT.md) for what each tier promises.",
    ]
    for tier in TIERS:
        lines += ["", f"## {tier.capitalize()}", "", " ".join(str(definitions.get(tier, "")).split())]
        for kind, heading in (("workflow", "Reusable workflows"), ("action", "Composite actions")):
            members = sorted(
                (c for c in components if c.tier == tier and c.kind == kind), key=lambda c: c.name
            )
            if not members:
                continue
            lines += ["", f"### {heading}", "", f"| {kind.capitalize()} | Description |", "| --- | --- |"]
            lines += [f"| [`{c.name}`]({link(c)}) | {_cell(c.description)} |" for c in members]
    return "\n".join(lines) + "\n"
