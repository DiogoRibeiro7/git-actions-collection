"""The audit must cover inline installer pins as well as dependency manifests."""

from scripts.security_requirements import collect_pins


def test_collects_action_workflow_and_example_pins_without_test_fixtures(tmp_path):
    files = {
        "scripts/install.sh": 'pip install requests==2.34.2 "tomlkit==0.13.3"\n',
        ".github/actions/setup/action.yml": 'inputs:\n  pip-version:\n    default: "26.2.1"\n',
        ".github/workflows/scan.yaml": (
            "on:\n  workflow_call:\n    inputs:\n      pip-version:\n        default: '26.2.1'\n"
            "jobs:\n  scan:\n    steps:\n      - run: pip install pip-audit==2.10.1\n"
        ),
        "examples/demo/pyproject.toml": '[project]\ndependencies = ["requests==2.34.2"]\n',
        "examples/demo/requirements.txt": "gunicorn==23.0.0\n",
        "tests/fixtures/old.sh": "pip install requests==2.0.0\n",
    }
    for filename, content in files.items():
        path = tmp_path / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    assert collect_pins(tmp_path) == [
        "gunicorn==23.0.0", "pip-audit==2.10.1", "pip==26.2.1",
        "requests==2.34.2", "tomlkit==0.13.3",
    ]


def test_latest_and_variable_installers_are_not_reported_as_exact_pins(tmp_path):
    path = tmp_path / ".github/actions/setup/action.yml"
    path.parent.mkdir(parents=True)
    path.write_text("inputs:\n  pip-version:\n    default: latest\n", encoding="utf-8")
    script = tmp_path / "scripts/install.sh"
    script.parent.mkdir()
    script.write_text('pip install "pip==$PIP_VERSION"\n', encoding="utf-8")
    assert collect_pins(tmp_path) == []
