import importlib.util
import json
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "sdu", Path(__file__).resolve().parents[1] / "scripts" / "smart_dependency_update.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules["sdu"] = MODULE
SPEC.loader.exec_module(MODULE)

bump_patch = MODULE.bump_patch
apply_updates = MODULE.apply_updates
parse_package_json = MODULE.parse_package_json
parse_pyproject = MODULE.parse_pyproject
parse_gemfile = MODULE.parse_gemfile
parse_gomod = MODULE.parse_gomod
gather_deps = MODULE.gather_deps
detect_conflicts = MODULE.detect_conflicts
_serialise_conflicts = MODULE._serialise_conflicts
main = MODULE.main


def test_bump_patch_preserves_prefixes():
    assert bump_patch("^1.2.3") == "^1.2.4"
    assert bump_patch("~=1.2.0") == "~=1.2.1"
    assert bump_patch("v1.2.3") == "v1.2.4"
    assert bump_patch(">=1.2.3") == ">=1.2.4"


def test_apply_updates_across_ecosystems(tmp_path):
    package = tmp_path / "js" / "package.json"
    package.parent.mkdir()
    package.write_text(json.dumps({"dependencies": {"left-pad": "^1.2.3"}}, indent=2))

    go_mod = tmp_path / "go" / "go.mod"
    go_mod.parent.mkdir()
    go_mod.write_text(
        """module example.com/demo

require (
    github.com/example/lib v1.2.3
)
"""
    )

    poetry_pyproject = tmp_path / "poetry" / "pyproject.toml"
    poetry_pyproject.parent.mkdir()
    poetry_pyproject.write_text(
        """[tool.poetry]
name = "demo"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.9"
pendulum = "1.2.3"
"""
    )

    pep_pyproject = tmp_path / "pep" / "pyproject.toml"
    pep_pyproject.parent.mkdir()
    pep_pyproject.write_text(
        """[project]
name = "pep-demo"
dependencies = [
    "requests >=1.2.3",
]
"""
    )

    results = apply_updates(
        [package, go_mod, poetry_pyproject, pep_pyproject],
        batch=10,
    )

    assert {r.name for r in results} == {
        "left-pad",
        "github.com/example/lib",
        "pendulum",
        "requests",
    }

    updated_versions = {r.name: r.updated for r in results}
    assert updated_versions["left-pad"] == "^1.2.4"
    assert updated_versions["github.com/example/lib"] == "v1.2.4"
    assert updated_versions["pendulum"] == "1.2.4"
    assert updated_versions["requests"] == ">=1.2.4"

    pkg_data = json.loads(package.read_text())
    assert pkg_data["dependencies"]["left-pad"] == "^1.2.4"

    go_contents = go_mod.read_text()
    assert "github.com/example/lib v1.2.4" in go_contents

    poetry_contents = poetry_pyproject.read_text()
    assert "pendulum = \"1.2.4\"" in poetry_contents

    pep_contents = pep_pyproject.read_text()
    assert ">=1.2.4" in pep_contents


def test_parse_helpers_handle_pep621(tmp_path):
    pyproj = tmp_path / "pyproject.toml"
    pyproj.write_text(
        """[project]
name = "pep-demo"
dependencies = ["requests>=1.2.3"]

[tool.poetry.dependencies]
python = "^3.9"
pendulum = { version = "1.2.3" }
"""
    )

    deps = parse_pyproject(pyproj)
    assert deps["requests"].startswith(">=")
    assert deps["pendulum"] == "1.2.3"


def test_main_outputs_serialisable_json(tmp_path, monkeypatch, capsys):
    package = tmp_path / "package.json"
    package.write_text(json.dumps({"dependencies": {"left-pad": "1.2.3"}}))

    monkeypatch.setattr(sys, "argv", ["smart", "--manifests", str(package), "--apply"])
    main()
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert payload["updates"][0]["manifest"] == str(package)
    assert payload["conflicts"] == {}


def test_detect_conflicts_flags_major_mismatch(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "demo"
dependencies = ["requests>=1.0"]
""",
        encoding="utf-8",
    )
    package = tmp_path / "package.json"
    package.write_text(json.dumps({"dependencies": {"requests": "^2.0.0"}}, indent=2))

    deps = gather_deps([pyproject, package])
    conflicts = detect_conflicts(deps)

    assert "requests" in conflicts
    serialised = _serialise_conflicts(conflicts)
    assert serialised["requests"][0]["manifest"].endswith("pyproject.toml")


def test_parse_gemfile_and_gomod(tmp_path):
    gemfile = tmp_path / "Gemfile"
    gemfile.write_text("gem 'rails', '7.1.2'\n", encoding="utf-8")
    gomod = tmp_path / "go.mod"
    gomod.write_text(
        """module example.com/demo

require (
    github.com/example/lib v1.2.3
)
""",
        encoding="utf-8",
    )

    assert parse_gemfile(gemfile)["rails"] == "7.1.2"
    assert parse_gomod(gomod)["github.com/example/lib"] == "v1.2.3"
