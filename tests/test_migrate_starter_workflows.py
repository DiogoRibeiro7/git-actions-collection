import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from scripts.migrate_starter_workflows import convert, detect_language, generate, main

PYTHON_STARTER = """\
name: Python package
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - run: pip install -r requirements.txt
      - run: pytest
"""

NODE_STARTER = """\
name: Node.js CI
on:
  push:
    branches: [ main ]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test
"""

def test_python_migration() -> None:
    migrated = convert(PYTHON_STARTER)
    assert 'python-test-matrix.yml@main' in migrated
    assert "python-versions: '[\"3.x\"]'" in migrated


def test_node_migration() -> None:
    migrated = convert(NODE_STARTER)
    assert 'node-ci.yml@main' in migrated
    assert "node-version: '20'" in migrated


def test_detect_language_missing_setup() -> None:
    broken = """\
name: Minimal
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "hi"
"""
    with pytest.raises(SystemExit):
        detect_language({"jobs": {"build": {"steps": [{"run": "echo hi"}]}}})


def test_generate_python_without_version() -> None:
    content = generate({"name": "Python CI", "on": {"push": None}}, "python", "")
    assert "python-test-matrix.yml@main" in content
    assert "python-versions" not in content


def test_main_refuses_overwrite(tmp_path, monkeypatch) -> None:
    starter = tmp_path / "starter.yml"
    starter.write_text(PYTHON_STARTER, encoding="utf-8")
    output = tmp_path / "output.yml"
    output.write_text("existing", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["migrate", str(starter), "-o", str(output)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert "Refusing to overwrite" in str(exc.value)
