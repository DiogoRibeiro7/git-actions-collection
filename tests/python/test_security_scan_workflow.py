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
    assert inputs["skip-python-scans"]["default"] is False
    assert inputs["dependency-install-command"]["default"] == ""
    assert inputs["bandit-args"]["default"] == "-ll -ii"
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
    assert "actions/download-artifact@37930b1c2abaa49bbe596cd826c3c89aef350131" in uses
    assert "actions/attest-build-provenance@ca0aaa1889e301c8331fbdb338d9475431b75b13" in uses


def test_security_scan_has_executable_self_test():
    workflow_path = Path(".github/workflows/test-security-scan.yml")
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["smoke"]
    assert smoke["uses"] == "./.github/workflows/security-scan.yml"
    assert smoke["with"] == {
        "paths": "tests/python/test_security_scan_workflow.py",
        "skip-python-scans": True,
        "skip-trivy": True,
        "skip-npm-signatures": True,
        "skip-java-verify": True,
        "skip-go-verify": True,
    }


def test_security_scan_can_audit_installed_consumer_dependencies():
    data = _load_workflow()
    steps = data["jobs"]["security"]["steps"]

    prepare = next(step for step in steps if step.get("name") == "Prepare Python dependency audit target")
    install = next(step for step in steps if step.get("name") == "Install Python scanners")
    scans = next(step for step in steps if step.get("name") == "Python dependency scans")

    assert prepare["env"]["DEPENDENCY_INSTALL_COMMAND"] == "${{ inputs.dependency-install-command }}"
    assert ".security-scan-audit-requirements.txt" in prepare["run"]
    assert "pip freeze --exclude-editable" in prepare["run"]

    assert "pip-audit==2.9.0" in install["run"]

    assert "--requirement .security-scan-audit-requirements.txt" in scans["run"]
    assert "pip-audit --strict --format sarif" in scans["run"]


def test_security_scan_passes_configurable_bandit_args():
    data = _load_workflow()
    steps = data["jobs"]["security"]["steps"]
    scans = next(step for step in steps if step.get("name") == "Python dependency scans")

    assert scans["env"]["BANDIT_ARGS"] == "${{ inputs.bandit-args }}"
    assert 'read -r -a bandit_args <<< "$BANDIT_ARGS"' in scans["run"]
    assert '"${bandit_args[@]}"' in scans["run"]
