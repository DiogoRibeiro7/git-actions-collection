from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Known GitHub Action refs retired from executable surfaces because their
# action metadata targets Node 16 or Node 20. Starter fixtures and docs are
# intentionally excluded because they may demonstrate migration from old
# workflows.
LEGACY_RUNTIME_REFS = {
    "actions/checkout@08eba0b27e820071cde6df949e0beb9ba4906955",
    "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
    "actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020",
    "actions/setup-java@387ac29b308b003ca37ba93a6cab5eb57c8f5f93",
    "actions/setup-go@d35c59abb061a4a6fb18e82ac0862c26744d6ab5",
    "actions/setup-go@1d76b952eb9246b03e20e15a9ef98c6d4af389ef",
    "actions/upload-artifact@330a01c490aca151604b8cf639adc76d48f6c5d4",
    "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093",
    "actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830",
    "actions/cache@0400d5f644dc74513175e3cd8d07132dd4860809",
    "github/codeql-action/upload-sarif@ad2a4837011b42f6947b78d6417e7c253b1c504b",
    "github/codeql-action/init@ad2a4837011b42f6947b78d6417e7c253b1c504b",
    "peter-evans/create-pull-request@4e1beaa7521e8b457b572c090b25bd3db56bf1c5",
    "gradle/actions/setup-gradle@6cfc8b8e8bb586cc164bef1c478c1eea3a4d6a19",
    "gitleaks/gitleaks-action@ff98106e4c7b2bc287b24eaf42907196329070c7",
    "actions/checkout@v4",
    "actions/setup-python@v5",
    "actions/setup-node@v4",
    "actions/upload-artifact@v4",
    "actions/cache@v4",
    "actions/download-artifact@v5",
}


def _executable_surfaces() -> list[Path]:
    paths = [
        *ROOT.glob(".github/actions/*/action.yml"),
        *ROOT.glob(".github/actions/*/action.yaml"),
        *ROOT.glob(".github/workflows/*.yml"),
        *ROOT.glob(".github/workflows/*.yaml"),
        *ROOT.glob("examples/**/.github/workflows/*.yml"),
        *ROOT.glob("examples/**/.github/workflows/*.yaml"),
        ROOT / "scripts" / "_lib" / "workflows.py",
    ]
    return sorted(path for path in paths if path.is_file())


def test_executable_surfaces_do_not_use_retired_node_runtimes() -> None:
    offenders: list[str] = []

    for path in _executable_surfaces():
        content = path.read_text(encoding="utf-8")
        for legacy_ref in sorted(LEGACY_RUNTIME_REFS):
            if legacy_ref in content:
                offenders.append(f"{path.relative_to(ROOT)}: {legacy_ref}")

    assert not offenders, (
        "Executable action/workflow surfaces still reference retired Node runtimes:\n"
        + "\n".join(offenders)
    )
