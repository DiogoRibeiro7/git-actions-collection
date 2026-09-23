from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"


def _sarif_run(
    *,
    tool_name: str,
    information_uri: str,
    rules: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "informationUri": information_uri,
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }


def _sarif_level(severity: str) -> str:
    normalized = severity.strip().lower()
    if normalized == "high":
        return "error"
    if normalized == "medium":
        return "warning"
    return "note"


def convert_bandit(payload: dict[str, Any]) -> dict[str, Any]:
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    raw_results = payload.get("results", [])
    if not isinstance(raw_results, list):
        raw_results = []

    for finding in raw_results:
        if not isinstance(finding, dict):
            continue

        rule_id = str(finding.get("test_id") or "BANDIT")
        issue_text = str(finding.get("issue_text") or "Bandit finding")
        test_name = str(finding.get("test_name") or rule_id)
        more_info = str(finding.get("more_info") or "")
        severity = str(finding.get("issue_severity") or "LOW")
        filename = str(finding.get("filename") or "")
        line_number = finding.get("line_number")

        if rule_id not in rules:
            rule: dict[str, Any] = {
                "id": rule_id,
                "shortDescription": {"text": test_name},
            }
            if more_info:
                rule["helpUri"] = more_info
            rules[rule_id] = rule

        result: dict[str, Any] = {
            "ruleId": rule_id,
            "level": _sarif_level(severity),
            "message": {"text": issue_text},
        }

        if filename:
            region: dict[str, Any] = {}
            if isinstance(line_number, int) and line_number > 0:
                region["startLine"] = line_number

            physical_location: dict[str, Any] = {
                "artifactLocation": {"uri": filename.replace("\\", "/")}
            }
            if region:
                physical_location["region"] = region

            result["locations"] = [{"physicalLocation": physical_location}]

        results.append(result)

    return _sarif_run(
        tool_name="Bandit",
        information_uri="https://bandit.readthedocs.io/",
        rules=list(rules.values()),
        results=results,
    )


def _pip_audit_dependencies(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        dependencies = payload.get("dependencies", [])
    elif isinstance(payload, list):
        dependencies = payload
    else:
        dependencies = []

    return [item for item in dependencies if isinstance(item, dict)]


def convert_pip_audit(payload: Any) -> dict[str, Any]:
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    for dependency in _pip_audit_dependencies(payload):
        package = str(dependency.get("name") or "unknown-package")
        version = str(dependency.get("version") or "unknown-version")
        vulnerabilities = dependency.get("vulns", [])
        if not isinstance(vulnerabilities, list):
            continue

        for vulnerability in vulnerabilities:
            if not isinstance(vulnerability, dict):
                continue

            vuln_id = str(vulnerability.get("id") or "PIP-AUDIT")
            description = str(vulnerability.get("description") or "Known vulnerability")
            aliases = vulnerability.get("aliases", [])
            fixes = vulnerability.get("fix_versions", [])

            if vuln_id not in rules:
                rule: dict[str, Any] = {
                    "id": vuln_id,
                    "shortDescription": {"text": description[:200]},
                }
                if isinstance(aliases, list) and aliases:
                    rule["properties"] = {"aliases": [str(alias) for alias in aliases]}
                rules[vuln_id] = rule

            message = f"{package} {version} is affected by {vuln_id}."
            if isinstance(fixes, list) and fixes:
                message += " Fixed in: " + ", ".join(str(item) for item in fixes) + "."

            results.append(
                {
                    "ruleId": vuln_id,
                    "level": "error",
                    "message": {"text": message},
                    "properties": {
                        "package": package,
                        "version": version,
                    },
                }
            )

    return _sarif_run(
        tool_name="pip-audit",
        information_uri="https://pypi.org/project/pip-audit/",
        rules=list(rules.values()),
        results=results,
    )


def convert_report(tool: str, source: Path, destination: Path) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))

    if tool == "bandit":
        if not isinstance(payload, dict):
            raise ValueError("Bandit JSON report must be an object")
        sarif = convert_bandit(payload)
    elif tool == "pip-audit":
        sarif = convert_pip_audit(payload)
    else:
        raise ValueError(f"Unsupported tool: {tool}")

    destination.write_text(
        json.dumps(sarif, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert security scanner JSON reports to SARIF")
    parser.add_argument("tool", choices=("bandit", "pip-audit"))
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    convert_report(args.tool, args.source, args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
