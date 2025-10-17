import yaml
from pathlib import Path

DEFAULT_PIP = "24.3.1"

COMPOSITE_ACTIONS = [
    Path(".github/actions/aws-lambda-build/action.yml"),
    Path(".github/actions/benchmark-smoke/action.yml"),
    Path(".github/actions/check-imports/action.yml"),
    Path(".github/actions/python-lint/action.yml"),
    Path(".github/actions/python-type-check/action.yml"),
    Path(".github/actions/setup-poetry/action.yml"),
    Path(".github/actions/smart-dependency-update/action.yml"),
]

REUSABLE_WORKFLOWS = [
    Path(".github/workflows/aws-lambda-deploy.yml"),
    Path(".github/workflows/coverage-report.yml"),
    Path(".github/workflows/database-migration.yml"),
    Path(".github/workflows/lockfile-consistency.yml"),
    Path(".github/workflows/publish-to-pypi.yml"),
    Path(".github/workflows/pypi-publish.yml"),
    Path(".github/workflows/python-lint.yml"),
    Path(".github/workflows/python-test-matrix.yml"),
    Path(".github/workflows/security-scan.yml"),
]


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _workflow_call_block(document: dict) -> dict | None:
    on_section = document.get("on")
    if on_section is None:
        # YAML 1.1 treats "on" as a boolean keyword unless quoted.
        on_section = document.get(True)
    if isinstance(on_section, dict):
        return on_section.get("workflow_call")
    return None


def test_composite_actions_expose_configurable_pip_version():
    for path in COMPOSITE_ACTIONS:
        data = load_yaml(path)
        inputs = data.get("inputs")
        assert inputs is not None, f"{path} must define inputs"
        pip_input = inputs.get("pip-version")
        assert pip_input is not None, f"{path} missing pip-version input"
        assert pip_input.get("default") == DEFAULT_PIP, (
            f"{path} should default pip-version to {DEFAULT_PIP}"
        )
        text = read_text(path)
        assert "inputs.pip-version" in text, (
            f"{path} must reference inputs.pip-version in its steps"
        )


def test_reusable_workflows_expose_configurable_pip_version():
    for path in REUSABLE_WORKFLOWS:
        data = load_yaml(path)
        call = _workflow_call_block(data)
        assert call is not None, f"{path} must be invocable via workflow_call"
        inputs = call.get("inputs")
        assert inputs is not None and "pip-version" in inputs, (
            f"{path} must expose a pip-version input"
        )
        assert inputs["pip-version"].get("default") == DEFAULT_PIP, (
            f"{path} should default pip-version to {DEFAULT_PIP}"
        )
        text = read_text(path)
        assert "inputs.pip-version" in text, (
            f"{path} must reference inputs.pip-version in its steps"
        )
