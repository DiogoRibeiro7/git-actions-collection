"""security-scan lists every applicable scanner and its findings on the run page."""

import json
import os
from pathlib import Path
import shutil
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import ActionResult, run_workflow_step

WORKFLOW = Path(".github/workflows/security-scan.yml")
FIXTURES = Path("tests/fixtures/security-scan")
SKIPS = {
    "skip-python-scans": False,
    "skip-trivy": True,
    "skip-npm-signatures": False,
    "skip-java-verify": False,
    "skip-go-verify": False,
}
HEADER = "## Security scan\n\n| Check | Result |\n| --- | --- |\n"
posix_only = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")


def _summary(workdir: Path, steps: dict[str, Any], **skips: bool) -> ActionResult:
    context = {"toJSON(steps)": json.dumps(steps)}
    for name, default in SKIPS.items():
        context[f"inputs.{name}"] = str(skips.get(name.replace("-", "_"), default)).lower()
    result = run_workflow_step(WORKFLOW, "security", "Summary", context=context, workdir=workdir)
    assert result.code == 0, result.stderr
    assert "Could not write the summary" not in result.stdout, result.stderr
    return result


def _scans(audit: str, bandit: str) -> dict[str, Any]:
    outputs = {"pip-audit-status": audit, "bandit-status": bandit}
    return {"python-scans": {"outcome": "success", "outputs": outputs}}


def test_summary_runs_after_the_uploads_and_before_the_final_failure() -> None:
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["security"]["steps"]
    names = [step.get("name") for step in steps]
    summary = steps[names.index("Summary")]

    assert names.index("Upload Trivy report") < names.index("Summary")
    assert names.index("Summary") == names.index("Fail on Python scanner findings") - 1
    assert summary["if"] == "${{ always() }}"
    assert summary["env"]["STEPS"] == "${{ toJSON(steps) }}"


@posix_only
def test_summary_lists_pip_audit_and_bandit_findings(tmp_path: Path) -> None:
    """The fixtures are real pip-audit 2.10.1 and Bandit 1.8.6 output (pip-audit's trimmed)."""
    for name in ("pip-audit.json", "bandit.json"):
        shutil.copy(FIXTURES / name, tmp_path / name)

    result = _summary(tmp_path, _scans("1", "1"))

    # pip-audit lists PYSEC-2019-217 twice, from two sources.
    assert result.summary == HEADER + """\
| pip-audit | ❌ Failed: 2 advisories in 1 package |
| Bandit | ❌ Failed: 1 high, 1 medium |

**pip-audit findings**

| Package | Version | Advisory | Fixed in |
| --- | --- | --- | --- |
| `jinja2` | 2.10 | [PYSEC-2021-66](https://osv.dev/vulnerability/PYSEC-2021-66) (CVE-2020-28493) \
| `2.11.3` |
| `jinja2` | 2.10 | [PYSEC-2019-217](https://osv.dev/vulnerability/PYSEC-2019-217) (CVE-2019-10906) \
| `2.10.1` |

**Bandit findings**

| Severity | Test | Location | Issue |
| --- | --- | --- | --- |
| HIGH | [B602](https://bandit.readthedocs.io/en/1.8.6/plugins/\
b602_subprocess_popen_with_shell_equals_true.html) subprocess_popen_with_shell_equals_true \
| `src/app.py:7` | subprocess call with shell=True identified, security issue. |
| MEDIUM | [B506](https://bandit.readthedocs.io/en/1.8.6/plugins/b506_yaml_load.html) yaml_load \
| `src/app.py:11` | Use of unsafe yaml load. Allows instantiation of arbitrary objects. \
Consider yaml.safe_load(). |
"""


@posix_only
def test_summary_lists_only_the_checks_that_apply(tmp_path: Path) -> None:
    clean_audit = {"dependencies": [{"name": "six", "version": "1.16.0", "vulns": []}]}
    (tmp_path / "pip-audit.json").write_text(json.dumps(clean_audit), encoding="utf-8")
    (tmp_path / "bandit.json").write_text('{"results": [], "errors": []}', encoding="utf-8")
    trivy = {"runs": [{
        "tool": {"driver": {"rules": [{
            "id": "CVE-2019-10906",
            "shortDescription": {"text": "jinja2: str.format_map allows sandbox escape"},
        }]}},
        "results": [{
            "ruleId": "CVE-2019-10906",
            "level": "error",
            "message": {"text": "Package: jinja2\nInstalled Version: 2.10"},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "requirements.txt"}, "region": {"startLine": 1},
            }}],
        }],
    }]}
    (tmp_path / "trivy.sarif").write_text(json.dumps(trivy), encoding="utf-8")
    for manifest in ("package-lock.json", "pom.xml", "build.gradle", "go.sum"):
        (tmp_path / manifest).write_text("", encoding="utf-8")
    steps = {
        **_scans("0", "0"),
        "trivy": {"outcome": "failure"},
        "npm-signatures": {"outcome": "success"},
        "maven": {"outcome": "failure"},
        "gradle": {"outcome": "success"},
        "go-modules": {"outcome": "skipped"},
    }

    result = _summary(tmp_path, steps, skip_trivy=False)

    # Without committed checksums the Gradle step warns and passes; the summary says so.
    assert result.summary == HEADER + """\
| pip-audit | ✅ Passed: 1 package audited |
| Bandit | ✅ Passed |
| Trivy | ❌ Failed: 1 finding |
| npm signatures | ✅ Passed |
| Maven dependencies | ❌ Failed |
| Gradle dependencies | ⚠️ Not verified: no gradle/verification-metadata.xml |
| Go modules | Skipped |

**Trivy findings**

| Rule | Level | Location | Description |
| --- | --- | --- | --- |
| CVE-2019-10906 | error | `requirements.txt:1` | jinja2: str.format_map allows sandbox escape |
"""


@posix_only
@pytest.mark.parametrize(
    ("steps", "bandit", "expected"),
    [
        # The scan step never ran, e.g. because installing the scanners failed.
        ({}, None, "| pip-audit | Not run |\n| Bandit | Not run |\n"),
        # A scanner error, not a finding: point at the logs.
        (
            _scans("2", "0"),
            {"results": [], "errors": [{"filename": "./broken.py", "reason": "syntax error"}]},
            "| pip-audit | ❌ Failed: exit 2, see the security-reports artifact |\n"
            "| Bandit | ✅ Passed (1 file could not be scanned) |\n",
        ),
    ],
)
def test_summary_without_findings_to_list(
    tmp_path: Path, steps: dict[str, Any], bandit: dict[str, Any] | None, expected: str
) -> None:
    if bandit is not None:
        (tmp_path / "bandit.json").write_text(json.dumps(bandit), encoding="utf-8")

    result = _summary(tmp_path, steps)

    assert result.summary == HEADER + expected


@posix_only
def test_summary_when_every_scanner_is_disabled(tmp_path: Path) -> None:
    result = _summary(
        tmp_path, {}, skip_python_scans=True, skip_npm_signatures=True,
        skip_java_verify=True, skip_go_verify=True,
    )

    assert result.summary == HEADER + "| (none) | Every scanner is disabled |\n"
