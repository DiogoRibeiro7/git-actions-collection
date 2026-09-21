from pathlib import Path

import yaml


def test_security_scan_inputs_defaults():
    workflow_path = Path(".github/workflows/security-scan.yml")
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    on_block = data.get("on") or data.get(True)
    inputs = on_block["workflow_call"]["inputs"]
    assert inputs["paths"]["default"] == "."
    assert inputs["skip-trivy"]["default"] is True
    assert inputs["pip-version"]["default"] == "24.3.1"
    assert inputs["skip-npm-signatures"]["default"] is False
    assert inputs["skip-java-verify"]["default"] is False
    assert inputs["skip-go-verify"]["default"] is False


def test_security_scan_permissions():
    workflow_path = Path(".github/workflows/security-scan.yml")
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    permissions = data["permissions"]
    assert permissions["contents"] == "read"
    assert permissions["security-events"] == "write"
