import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

SPEC = importlib.util.spec_from_file_location(
    "migrate",
    Path(__file__).resolve().parents[2] / "scripts" / "migrate_starter_workflows.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules["migrate"] = MODULE
SPEC.loader.exec_module(MODULE)

from scripts._lib.workflows import convert, detect_language, generate_migrated


@pytest.fixture()
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "workflows"


def test_detect_language_python(fixtures_dir: Path):
    data = yaml.safe_load((fixtures_dir / "starter_python.yml").read_text())
    lang, version = detect_language(data)
    assert lang == "python"
    assert version == "3.x"


def test_convert_python_matches_fixture(fixtures_dir: Path):
    content = (fixtures_dir / "starter_python.yml").read_text(encoding="utf-8")
    expected = (fixtures_dir / "migrated_python.yml").read_text(encoding="utf-8")
    assert yaml.safe_load(convert(content)) == yaml.safe_load(expected)


def test_convert_node_matches_fixture(fixtures_dir: Path):
    content = (fixtures_dir / "starter_node.yml").read_text(encoding="utf-8")
    expected = (fixtures_dir / "migrated_node.yml").read_text(encoding="utf-8")
    assert yaml.safe_load(convert(content)) == yaml.safe_load(expected)


def test_invalid_yaml_raises():
    with pytest.raises(SystemExit):
        convert("[not: yaml")


def test_round_trip_required_nodes(fixtures_dir: Path):
    content = (fixtures_dir / "starter_python.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(convert(content))
    assert "jobs" in data
    assert "on" in data
    assert "name" in data


def test_cli_output_path_override(tmp_path: Path, monkeypatch, fixtures_dir: Path):
    starter = tmp_path / "starter.yml"
    starter.write_text((fixtures_dir / "starter_python.yml").read_text(), encoding="utf-8")
    out = tmp_path / "out.yml"

    monkeypatch.setattr(sys, "argv", ["migrate", str(starter), "-o", str(out)])
    MODULE.main()

    assert out.exists()


def test_generate_migrated_preserves_triggers(fixtures_dir: Path):
    data = yaml.safe_load((fixtures_dir / "starter_node.yml").read_text())
    migrated = generate_migrated(data, "node", "20")
    parsed = yaml.safe_load(migrated)
    assert parsed["on"] == data["on"]


def test_convert_preserves_triggers_when_on_is_boolean_key(fixtures_dir: Path):
    content = (
        "name: Demo\n"
        "on: [push]\n\n"
        "jobs:\n"
        "  build:\n"
        "    steps:\n"
        "      - uses: actions/setup-python@v4\n"
        "        with:\n"
        "          python-version: '3.11'\n"
    )
    data = yaml.safe_load(content)
    assert True in data
    migrated = yaml.safe_load(convert(content))
    assert migrated["on"] == data[True]


def test_convert_python_with_permissions(fixtures_dir: Path):
    content = (fixtures_dir / "starter_python_with_permissions.yml").read_text(encoding="utf-8")
    expected = (fixtures_dir / "migrated_python_with_permissions.yml").read_text(encoding="utf-8")
    assert yaml.safe_load(convert(content)) == yaml.safe_load(expected)


def test_convert_unknown_language_raises(fixtures_dir: Path):
    content = (fixtures_dir / "starter_unknown.yml").read_text(encoding="utf-8")
    with pytest.raises(SystemExit):
        convert(content)
