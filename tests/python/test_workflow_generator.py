import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

SPEC = importlib.util.spec_from_file_location(
    "workflow_generator",
    Path(__file__).resolve().parents[2] / "scripts" / "workflow_generator.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules["workflow_generator"] = MODULE
SPEC.loader.exec_module(MODULE)

from scripts._lib.workflows import node_workflow, python_workflow


@pytest.fixture()
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "workflows"


def test_python_workflow_deterministic(fixtures_dir: Path):
    expected = (fixtures_dir / "generated_python.yml").read_text(encoding="utf-8")
    assert yaml.safe_load(python_workflow("main")) == yaml.safe_load(expected)


def test_node_workflow_deterministic(fixtures_dir: Path):
    expected = (fixtures_dir / "generated_node.yml").read_text(encoding="utf-8")
    assert yaml.safe_load(node_workflow("main")) == yaml.safe_load(expected)


def test_branch_override(tmp_path: Path):
    content = python_workflow("develop")
    assert "branches: [develop]" in content


def test_output_path_override(tmp_path: Path, monkeypatch):
    out = tmp_path / "custom.yml"
    monkeypatch.setattr(sys, "argv", ["workflow-generator", "python", "-o", str(out)])
    MODULE.main()
    assert out.exists()


def test_round_trip_parses():
    content = node_workflow("main")
    data = yaml.safe_load(content)
    assert "jobs" in data
    assert "on" in data
    assert "permissions" in data


def test_generator_on_key_is_string():
    data = yaml.safe_load(python_workflow("main"))
    assert "on" in data
    assert True not in data
