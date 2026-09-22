from __future__ import annotations

from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / ".github" / "support-matrix.yml"
SHA_REF = re.compile(r"^[0-9a-f]{40}$")


def _load_matrix() -> dict:
    return yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8"))


def test_all_composite_actions_are_classified_once() -> None:
    matrix = _load_matrix()
    actions = matrix["composite_actions"]

    classified = [
        name
        for tier in ("supported", "reference", "experimental")
        for name in actions[tier]
    ]
    actual = sorted(
        path.name
        for path in (ROOT / ".github" / "actions").iterdir()
        if path.is_dir() and (path / "action.yml").exists()
    )

    assert len(classified) == len(set(classified)), "composite action appears in multiple tiers"
    assert sorted(classified) == actual


def test_supported_composite_actions_have_contract_tests() -> None:
    matrix = _load_matrix()
    exceptions = {
        "check-imports": "test_check_imports_contract.bats",
        "smart-dependency-update": "test_smart_dependency_update_contract.bats",
    }

    for name in matrix["composite_actions"]["supported"]:
        filename = exceptions.get(name, f"test_{name.replace('-', '_')}.bats")
        path = ROOT / "tests" / "bash" / "actions" / filename
        assert path.exists(), f"supported action {name} lacks contract test {path}"


def test_supported_composite_actions_pin_external_dependencies() -> None:
    matrix = _load_matrix()

    for name in matrix["composite_actions"]["supported"]:
        path = ROOT / ".github" / "actions" / name / "action.yml"
        document = yaml.safe_load(path.read_text(encoding="utf-8"))

        for step in document.get("runs", {}).get("steps", []):
            uses = step.get("uses")
            if not isinstance(uses, str):
                continue
            if uses.startswith("./") or uses.startswith("DiogoRibeiro7/git-actions-collection/"):
                continue

            assert "@" in uses, f"{path}: external action reference has no ref: {uses}"
            _, ref = uses.rsplit("@", 1)
            assert SHA_REF.fullmatch(ref), (
                f"{path}: supported actions must pin external dependencies to a 40-char SHA: {uses}"
            )


def test_all_workflows_are_classified_once() -> None:
    matrix = _load_matrix()
    workflows = matrix["workflows"]

    supported = list(workflows["supported"].keys())
    classified = (
        supported
        + workflows["reference"]
        + workflows["experimental"]
        + workflows["internal"]
    )
    actual = sorted(path.name for path in (ROOT / ".github" / "workflows").glob("*.yml"))

    assert len(classified) == len(set(classified)), "workflow appears in multiple support tiers"
    assert sorted(classified) == actual


def test_supported_workflow_evidence_exists() -> None:
    matrix = _load_matrix()

    for workflow, metadata in matrix["workflows"]["supported"].items():
        workflow_path = ROOT / ".github" / "workflows" / workflow
        assert workflow_path.exists()

        evidence = metadata.get("evidence", [])
        assert evidence, f"supported workflow {workflow} must declare evidence"
        for relative in evidence:
            assert (ROOT / relative).exists(), f"missing support evidence for {workflow}: {relative}"
