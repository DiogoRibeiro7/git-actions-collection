import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from scripts._lib.migration import load_workflow, plan_migration
from scripts.migrate_starter_workflows import convert, main

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

YARN_STARTER = """\
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
      - run: yarn install --immutable
      - run: yarn test
"""


def test_python_migration() -> None:
    migrated = convert(PYTHON_STARTER)
    assert "python-test-matrix.yml@v1" in migrated
    assert "python-versions: '[\"3.x\"]'" in migrated


def test_yarn_node_migration() -> None:
    migrated = convert(YARN_STARTER)
    assert "node-ci.yml@v1" in migrated
    assert "node-version: '20'" in migrated


def test_missing_setup_step_is_not_migrated() -> None:
    with pytest.raises(SystemExit, match="Unable to detect language"):
        plan_migration({"jobs": {"build": {"steps": [{"run": "echo hi"}]}}})


def test_python_without_version_uses_the_default_versions() -> None:
    plan = plan_migration(
        load_workflow(
            "name: Python CI\non: push\njobs:\n  b:\n    steps:\n"
            "      - uses: actions/setup-python@v5\n"
        )
    )
    assert plan.uses and "python-test-matrix.yml@v1" in plan.uses
    assert "python-versions" not in plan.inputs


def test_main_refuses_overwrite(tmp_path) -> None:
    starter = tmp_path / "starter.yml"
    starter.write_text(PYTHON_STARTER, encoding="utf-8")
    output = tmp_path / "output.yml"
    output.write_text("existing", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        main([str(starter), "-o", str(output)])
    assert "Refusing to overwrite" in str(exc.value)
    assert output.read_text(encoding="utf-8") == "existing"
