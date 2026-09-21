from pathlib import Path

import yaml


def test_python_test_matrix_inputs_defaults():
    workflow_path = Path(".github/workflows/python-test-matrix.yml")
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    on_block = data.get("on") or data.get(True)
    inputs = on_block["workflow_call"]["inputs"]
    assert inputs["python-versions"]["default"] == '["3.10","3.11","3.12"]'
    assert inputs["os-matrix"]["default"] == '["ubuntu-latest","windows-latest","macos-latest"]'
    assert inputs["test-command"]["default"] == "pytest -q"
    assert inputs["pip-version"]["default"] == "24.3.1"


def test_python_test_matrix_strategy_uses_inputs():
    workflow_path = Path(".github/workflows/python-test-matrix.yml")
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    matrix = data["jobs"]["test"]["strategy"]["matrix"]
    assert "fromJson(inputs.python-versions)" in matrix["python"]
    assert "fromJson(inputs.os-matrix)" in matrix["os"]
