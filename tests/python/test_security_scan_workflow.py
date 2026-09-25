from pathlib import Path

import yaml

from tests.utils.action_refs import action_name, is_commit_pinned


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
    assert inputs["pip-version"]["default"] == "26.2.1"
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
        action_name(step.get("uses")) != "actions/attest-build-provenance"
        for step in scan_steps
    )

    provenance_steps = data["jobs"]["provenance"]["steps"]
    uses = [step["uses"] for step in provenance_steps if "uses" in step]
    assert any(is_commit_pinned(ref, "actions/download-artifact") for ref in uses)
    assert any(is_commit_pinned(ref, "actions/attest-build-provenance") for ref in uses)


def test_security_scan_has_executable_self_test():
    workflow_path = Path(".github/workflows/test-security-scan.yml")
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    smoke = data["jobs"]["smoke"]
    assert smoke["uses"] == "./.github/workflows/security-scan.yml"
    # The Python scans run for real: they audit this repository's pyproject.toml.
    assert smoke["with"] == {
        "paths": "tests/python/test_security_scan_workflow.py",
        "skip-python-scans": False,
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

    assert 'python -m venv "$RUNNER_TEMP/security-scan-tools"' in install["run"]
    assert "pip-audit==2.10.1" in install["run"]
    assert "bandit==1.8.6" in install["run"]

    assert scans["env"]["AUDIT_REQUIREMENTS"] == "${{ steps.audit-target.outputs.requirements }}"
    assert '--requirement "$AUDIT_REQUIREMENTS"' in scans["run"]
    assert "--format json" in scans["run"]
    assert "-f json -o bandit.json" in scans["run"]
    assert "--format sarif" not in scans["run"]
    assert "-f sarif" not in scans["run"]


def test_security_scan_passes_configurable_bandit_args():
    data = _load_workflow()
    steps = data["jobs"]["security"]["steps"]
    scans = next(step for step in steps if step.get("name") == "Python dependency scans")

    assert scans["env"]["BANDIT_ARGS"] == "${{ inputs.bandit-args }}"
    assert 'read -r -a bandit_args <<< "$BANDIT_ARGS"' in scans["run"]
    assert '"${bandit_args[@]}"' in scans["run"]


def test_security_scan_converts_reports_before_failing_findings():
    data = _load_workflow()
    steps = data["jobs"]["security"]["steps"]
    names = [step.get("name") for step in steps]

    convert_index = names.index("Convert Python scanner reports to SARIF")
    pip_upload_index = names.index("Upload pip-audit report")
    bandit_upload_index = names.index("Upload Bandit report")
    fail_index = names.index("Fail on Python scanner findings")

    assert convert_index < pip_upload_index < fail_index
    assert convert_index < bandit_upload_index < fail_index

    convert = steps[convert_index]["run"]
    assert 'Path("pip-audit.sarif").write_text' in convert
    assert 'Path("bandit.sarif").write_text' in convert

    fail = steps[fail_index]
    assert fail["env"]["PIP_AUDIT_STATUS"] == "${{ steps.python-scans.outputs.pip-audit-status }}"
    assert fail["env"]["BANDIT_STATUS"] == "${{ steps.python-scans.outputs.bandit-status }}"
    assert "exit 1" in fail["run"]


def test_python_scanners_do_not_mutate_consumer_environment():
    data = _load_workflow()
    steps = data["jobs"]["security"]["steps"]
    install = next(step for step in steps if step.get("name") == "Install Python scanners")

    assert '"$RUNNER_TEMP/security-scan-tools/bin/python" -m pip install' in install["run"]
    assert not any(
        line.strip().startswith("python -m pip install pip-audit")
        for line in install["run"].splitlines()
    )
