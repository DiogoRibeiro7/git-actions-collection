from __future__ import annotations

from pathlib import Path
import tomllib

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_v1_project_metadata_is_stable() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == "1.0.0"
    assert "Development Status :: 5 - Production/Stable" in data["project"]["classifiers"]


def test_generators_default_to_v1() -> None:
    workflows = (ROOT / "scripts" / "_lib" / "workflows.py").read_text(encoding="utf-8")
    wizard = (ROOT / "scripts" / "pypi_trusted_publishing_wizard.py").read_text(
        encoding="utf-8"
    )
    assert 'CONSUMER_REF = "v1"' in workflows
    assert "pypi-publish.yml@v1" in wizard


def test_supported_action_docs_use_v1_not_main() -> None:
    matrix = yaml.safe_load((ROOT / ".github" / "support-matrix.yml").read_text(encoding="utf-8"))
    for action in matrix["composite_actions"]["supported"]:
        readme = ROOT / ".github" / "actions" / action / "README.md"
        if not readme.exists():
            continue
        content = readme.read_text(encoding="utf-8")
        assert "DiogoRibeiro7/git-actions-collection/" not in content or "@main" not in content


def test_supported_workflow_examples_use_v1() -> None:
    paths = [
        ROOT / "examples" / "django-app" / ".github" / "workflows" / "ci.yml",
        ROOT / "examples" / "security-scan" / ".github" / "workflows" / "security.yml",
        ROOT / "examples" / "python-package" / ".github" / "workflows" / "security.yml",
    ]
    for path in paths:
        content = path.read_text(encoding="utf-8")
        assert "python-test-matrix.yml@main" not in content
        assert "security-scan.yml@main" not in content


def test_internal_canary_workflow_uses_local_delegates() -> None:
    data = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "canary-release.yml").read_text(encoding="utf-8")
    )
    for job in ("python", "npm", "docker"):
        uses = data["jobs"][job]["uses"]
        assert uses.startswith("./.github/workflows/")
        assert "@main" not in uses
