import importlib.util
import json
import sys
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "sdu",
    Path(__file__).resolve().parents[2] / "scripts" / "smart_dependency_update.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules["sdu"] = MODULE
SPEC.loader.exec_module(MODULE)

apply_updates = MODULE.apply_updates
detect_conflicts = MODULE.detect_conflicts
gather_deps = MODULE.gather_deps


def test_apply_updates_emits_report(tmp_path):
    package = tmp_path / "package.json"
    package.write_text(json.dumps({"dependencies": {"left-pad": "1.2.3"}}), encoding="utf-8")

    results = apply_updates([package], batch=1)
    assert len(results) == 1
    assert results[0].name == "left-pad"
    assert results[0].updated.endswith(".4")


def test_detect_conflicts_major_split(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "demo"
dependencies = ["requests>=1.0"]
""",
        encoding="utf-8",
    )
    package = tmp_path / "package.json"
    package.write_text(json.dumps({"dependencies": {"requests": "^2.0.0"}}), encoding="utf-8")

    deps = gather_deps([pyproject, package])
    conflicts = detect_conflicts(deps)
    assert "requests" in conflicts


def test_apply_updates_respects_batch(tmp_path):
    package = tmp_path / "package.json"
    package.write_text(
        json.dumps(
            {"dependencies": {"left-pad": "1.2.3", "right-pad": "2.0.0"}},
            indent=2,
        ),
        encoding="utf-8",
    )

    results = apply_updates([package], batch=1)
    assert len(results) == 1
