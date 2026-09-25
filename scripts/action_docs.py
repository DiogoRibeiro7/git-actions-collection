#!/usr/bin/env python3
"""Keep each composite action's README Inputs and Outputs in sync with action.yml.

The section between the markers is generated from the action's metadata;
everything else in the README is written by hand. `--check` fails when a README
is stale, and `--write` regenerates the section. A README without markers has
its hand-written `## Inputs` and `## Outputs` sections replaced on `--write`.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

ACTIONS = Path(".github/actions")
BEGIN = "<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->"
END = "<!-- END GENERATED REFERENCE -->"
REPLACED_SECTIONS = {"## Inputs", "## Outputs"}


def _cell(value: object) -> str:
    """Fit a value on one table row."""
    return " ".join(str(value).split()).replace("|", "\\|")


def _default(spec: Mapping[str, Any]) -> str:
    if "default" not in spec:
        return ""
    value = spec["default"]
    if isinstance(value, bool):
        value = str(value).lower()
    return f"`{_cell(value)}`" if str(value) != "" else '`""`'


def _required(spec: Mapping[str, Any]) -> str:
    return "yes" if str(spec.get("required", False)).lower() == "true" else "no"


def render_reference(metadata: Mapping[str, Any]) -> str:
    """Render the Inputs and Outputs sections for an action's metadata."""
    inputs = metadata.get("inputs") or {}
    outputs = metadata.get("outputs") or {}
    lines = [BEGIN, "## Inputs", ""]
    if inputs:
        lines += ["| Input | Required | Default | Description |", "| --- | --- | --- | --- |"]
        lines += [
            f"| `{name}` | {_required(spec or {})} | {_default(spec or {})} "
            f"| {_cell((spec or {}).get('description', ''))} |"
            for name, spec in inputs.items()
        ]
    else:
        lines.append("This action has no inputs.")
    lines += ["", "## Outputs", ""]
    if outputs:
        lines += ["| Output | Description |", "| --- | --- |"]
        lines += [
            f"| `{name}` | {_cell((spec or {}).get('description', ''))} |"
            for name, spec in outputs.items()
        ]
    else:
        lines.append("This action has no outputs.")
    return "\n".join([*lines, END])


def update_readme(readme: str, reference: str) -> str:
    """Return the README with its generated section replaced or inserted."""
    if BEGIN in readme and END in readme:
        before, _, rest = readme.partition(BEGIN)
        _, _, after = rest.partition(END)
        return before + reference + after

    # The generated section goes where `## Inputs` was, else before the first section.
    lines = readme.splitlines()
    headings = [i for i, line in enumerate(lines) if line.startswith("## ")]
    replaced = [i for i in headings if lines[i].strip() in REPLACED_SECTIONS]
    anchor = replaced[0] if replaced else headings[0] if headings else None
    kept: list[str] = []
    insert_at: int | None = None
    skipping = False
    for index, line in enumerate(lines):
        if line.startswith("## "):
            skipping = line.strip() in REPLACED_SECTIONS
        if index == anchor:
            insert_at = len(kept)
        if not skipping:
            kept.append(line)
    if insert_at is None:
        if kept and kept[-1].strip():
            kept.append("")
        insert_at = len(kept)
    block = reference.splitlines()
    if insert_at < len(kept):
        block.append("")
    return "\n".join([*kept[:insert_at], *block, *kept[insert_at:]]).rstrip("\n") + "\n"


def stale_readmes(root: Path, write: bool) -> list[str]:
    """List READMEs whose generated section differs from action.yml, fixing them if asked."""
    stale: list[str] = []
    for metadata_path in sorted((root / ACTIONS).glob("*/action.y*ml")):
        readme_path = metadata_path.parent / "README.md"
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
        if readme_path.exists():
            current = readme_path.read_text(encoding="utf-8")
            base = current
        else:
            current = ""
            base = f"# {metadata.get('name', metadata_path.parent.name)}\n\n{metadata.get('description', '')}\n"
        expected = update_readme(base, render_reference(metadata))
        if expected != current:
            stale.append(readme_path.relative_to(root).as_posix())
            if write:
                readme_path.write_text(expected, encoding="utf-8", newline="\n")
    return stale


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail when a README is stale")
    mode.add_argument("--write", action="store_true", help="regenerate stale READMEs")
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    args = parser.parse_args(argv)

    stale = stale_readmes(args.root, write=args.write)
    if args.write:
        print("\n".join(f"Updated {path}" for path in stale) or "Action READMEs are up to date.")
        return 0
    if stale:
        print("Action READMEs out of sync with action.yml (run with --write):")
        print("\n".join(f"  - {path}" for path in stale))
        return 1
    print("Action READMEs match action.yml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
