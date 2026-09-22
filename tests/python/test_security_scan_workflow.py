from pathlib import Path

import yaml


def _load_workflow() -> dict:
    workflow_path = Path(".github/workflows/security-scan.yml")
    return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))


def test_security_scan_inputs_defaults():
    data = _load_workflow()

    on_block = data.get("on") or data.get(True)
    inputs = on_block["workflow_call"]["inputs"]
    assert inputs["paths"]["default"] == "."
    assert inputs["skip-trivy"]["default"] is True
    assert inputs["pip-version"]["default"] == "24.3.1"
    assert inputs["skip-npm-signatures"]["default"] is False
    assert inputs["skip-java-verify"]["default"] is False
    assert inputs["skip-go-verify"]["default"] is False


def test_security_scan_uses_least_privilege_jobs():
    data = _load_workflow()

    assert data["permissions"] == {"contents": "read"}

    scan_permissions = data["jobs"]["security"]["permissions"]
    assert scan_permissions == {
        "contents": "read",
        "security-events": "write",
    }

    provenance_permissions = data["jobs"]["provenance"]["permissions"]
    assert provenance_permissions == {
        "contents": "read",
        "id-token": "write",
        "attestations": "write",
    }


def test_security_scan_provenance_is_isolated_from_scanners():
    data = _load_workflow()

    scan_steps = data["jobs"]["security"]["steps"]
    assert all(
        step.get("uses") != "actions/attest-build-provenance@ca0aaa1889e301c8331fbdb338d9475431b75b13"
        for step in scan_steps
    )

    provenance_steps = data["jobs"]["provenance"]["steps"]
    uses = {step.get("uses") for step in provenance_steps}
    assert "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093" in uses
    assert "actions/attest-build-provenance@ca0aaa1889e301c8331fbdb338d9475431b75b13" in uses
