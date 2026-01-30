import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "check_imports",
    Path(__file__).resolve().parents[2] / "scripts" / "check_imports_vs_pyproject.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules["check_imports"] = MODULE
SPEC.loader.exec_module(MODULE)


extract_top_level_imports = MODULE.extract_top_level_imports
load_pyproject_deps = MODULE.load_pyproject_deps
write_missing_to_pyproject = MODULE.write_missing_to_pyproject


@pytest.fixture()
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures"


def test_extract_top_level_imports(fixtures_dir: Path):
    imports = extract_top_level_imports(fixtures_dir / "sample_imports.py")
    assert "requests" in imports
    assert "httpx" in imports


def test_load_pyproject_deps(fixtures_dir: Path):
    deps = load_pyproject_deps(fixtures_dir / "pyproject_min.toml")
    assert any(dep.startswith("requests") for dep in deps)


def test_write_missing_to_pyproject(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]\nname = 'demo'\ndependencies = []\n""",
        encoding="utf-8",
    )
    cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        write_missing_to_pyproject(["httpx"])
    finally:
        os.chdir(cwd)
    contents = pyproject.read_text(encoding="utf-8")
    assert "httpx" in contents


def test_missing_vs_unused_summary(fixtures_dir: Path):
    expected = json.loads((fixtures_dir / "expected_missing.json").read_text())
    imports = extract_top_level_imports(fixtures_dir / "sample_imports.py")
    deps = load_pyproject_deps(fixtures_dir / "pyproject_min.toml")
    missing = sorted({"httpx"} - {d.replace("_", "-") for d in deps})
    unused = sorted({d.replace("_", "-") for d in deps} - {m.replace("_", "-") for m in imports})
    assert missing == expected["missing"]
    assert unused == expected["unused"]
