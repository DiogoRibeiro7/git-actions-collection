import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.migrate_starter_workflows import convert

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
