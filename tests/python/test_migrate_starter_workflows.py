import json
from pathlib import Path

import pytest
import yaml

from scripts._lib.migration import (
    convert,
    explain,
    load_workflow,
    plan_migration,
    render_migration,
)
from scripts.migrate_starter_workflows import main

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "workflows"
STARTERS = FIXTURES / "github-starters"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _plan(content: str, **options: str):
    return plan_migration(load_workflow(content), **options)


def test_convert_python_matches_fixture():
    expected = _read(FIXTURES / "migrated_python.yml")
    assert yaml.safe_load(convert(_read(FIXTURES / "starter_python.yml"))) == yaml.safe_load(
        expected
    )


def test_convert_yarn_node_matches_fixture():
    expected = _read(FIXTURES / "migrated_node_yarn.yml")
    migrated = convert(_read(FIXTURES / "starter_node_yarn.yml"))
    assert yaml.safe_load(migrated) == yaml.safe_load(expected)


def test_convert_python_with_permissions():
    content = _read(FIXTURES / "starter_python_with_permissions.yml")
    expected = _read(FIXTURES / "migrated_python_with_permissions.yml")
    assert yaml.safe_load(convert(content)) == yaml.safe_load(expected)


def test_github_python_starter_resolves_its_version_matrix():
    """The starter passes `${{ matrix.python-version }}`, which the migrated job
    cannot use: it has no matrix, so GitHub rejects the expression."""
    content = _read(STARTERS / "python-package.yml")
    plan = _plan(content)

    assert plan.inputs == {
        "python-versions": '["3.9", "3.10", "3.11"]',
        "os-matrix": '["ubuntu-latest"]',
        "test-command": "pytest",
    }
    assert any("python-lint.yml" in note for note in plan.notes)
    assert any("`Lint with flake8`" in note for note in plan.notes)
    assert yaml.safe_load(render_migration(plan)) == yaml.safe_load(
        _read(STARTERS / "python-package.migrated.yml")
    )
    assert "${{ matrix" not in render_migration(plan)


def test_default_branch_placeholder_is_replaced():
    plan = _plan(_read(STARTERS / "python-package.yml"), default_branch="trunk")

    assert plan.triggers["push"]["branches"] == ["trunk"]
    assert plan.triggers["pull_request"]["branches"] == ["trunk"]
    assert any("$default-branch" in note for note in plan.notes)


def test_github_node_starter_uses_npm_so_nothing_is_generated():
    """The tool migrates Yarn starters only so far."""
    plan = _plan(_read(STARTERS / "node.js.yml"))

    assert plan.ecosystem == "node"
    assert plan.workflow is None and plan.uses is None
    assert "uses npm" in explain(plan)
    with pytest.raises(SystemExit, match="Yarn only"):
        convert(_read(STARTERS / "node.js.yml"))


def test_npm_is_detected_from_commands_and_pnpm_from_its_setup_action():
    npm = _plan(_read(FIXTURES / "starter_node.yml"))
    pnpm = _plan(
        "on: push\njobs:\n  b:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: pnpm/action-setup@v4\n      - uses: actions/setup-node@v4\n"
        "      - run: pnpm test\n"
    )

    assert npm.workflow is None and "uses npm" in npm.notes[0]
    assert pnpm.workflow is None and "uses pnpm" in pnpm.notes[0]


def test_node_matrix_keeps_the_newest_version():
    plan = _plan(_read(FIXTURES / "starter_node_yarn.yml"))

    assert plan.inputs["node-version"] == "22.x"
    assert any("22.x is the newest of 18.x, 20.x, 22.x" in note for note in plan.notes)
    assert any("`yarn build`" in note for note in plan.notes)


def test_unquoted_versions_are_flagged():
    plan = _plan(
        "on: push\njobs:\n  b:\n    runs-on: ubuntu-latest\n"
        "    strategy:\n      matrix:\n        python-version: [3.9, 3.10]\n"
        "    steps:\n      - uses: actions/setup-python@v5\n"
        "        with:\n          python-version: ${{ matrix.python-version }}\n"
    )

    assert plan.inputs["python-versions"] == '["3.9", "3.1"]'
    assert any("3.10 became 3.1" in note for note in plan.notes)


def test_unresolvable_matrix_reference_falls_back_to_the_default():
    plan = _plan(
        "on: push\njobs:\n  b:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/setup-python@v5\n"
        "        with:\n          python-version: ${{ matrix.python }}\n"
    )

    assert "python-versions" not in plan.inputs
    assert any("Could not resolve" in note for note in plan.notes)


def test_os_matrix_follows_a_matrix_runner():
    plan = _plan(
        "on: push\njobs:\n  b:\n    runs-on: ${{ matrix.os }}\n"
        "    strategy:\n      matrix:\n        os: [ubuntu-latest, windows-latest]\n"
        "    steps:\n      - uses: actions/setup-python@v5\n"
        "        with:\n          python-version: '3.12'\n"
    )

    assert plan.inputs["os-matrix"] == '["ubuntu-latest", "windows-latest"]'


def test_other_jobs_with_other_ecosystems_are_noted():
    plan = _plan(
        "on: push\njobs:\n"
        "  api:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/setup-python@v5\n"
        "  web:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/setup-node@v4\n        with:\n          cache: yarn\n"
    )

    assert plan.ecosystem == "python"
    assert any("Also found node in job `web`" in note for note in plan.notes)


def test_convert_preserves_triggers_when_on_is_boolean_key():
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
    assert yaml.safe_load(convert(content))["on"] == data[True]


def test_invalid_yaml_raises():
    with pytest.raises(SystemExit):
        convert("[not: yaml")


def test_convert_unknown_language_raises():
    with pytest.raises(SystemExit, match="Unable to detect language"):
        convert(_read(FIXTURES / "starter_unknown.yml"))


def test_cli_writes_the_output_file(tmp_path: Path):
    out = tmp_path / "out.yml"

    main([str(FIXTURES / "starter_python.yml"), "-o", str(out)])

    assert yaml.safe_load(out.read_text(encoding="utf-8")) == yaml.safe_load(
        _read(FIXTURES / "migrated_python.yml")
    )


def test_cli_dry_run_explains_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    out = tmp_path / "out.yml"

    main([str(STARTERS / "python-package.yml"), "-o", str(out), "--dry-run"])

    printed = capsys.readouterr().out
    assert not out.exists()
    assert "Detected: python (job `build`)" in printed
    assert "python-test-matrix.yml@v1" in printed
    assert "No files were written (dry run)." in printed


def test_cli_json_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    out = tmp_path / "out.yml"

    main([str(STARTERS / "python-package.yml"), "-o", str(out), "--json"])

    report = json.loads(capsys.readouterr().out)
    assert report["ecosystem"] == "python"
    assert report["workflow"] == "python-test-matrix.yml"
    assert report["inputs"]["python-versions"] == '["3.9", "3.10", "3.11"]'
    assert report["output"] == str(out)
    assert report["migrated"] == out.read_text(encoding="utf-8")


def test_cli_reports_a_starter_it_cannot_migrate(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as exited:
        main([str(STARTERS / "node.js.yml"), "--json"])

    report = json.loads(capsys.readouterr().out)
    assert exited.value.code == 1
    assert report["workflow"] is None and report["migrated"] is None
    assert any("Yarn only" in note for note in report["notes"])


def test_cli_explains_a_starter_it_cannot_migrate_on_stderr(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as exited:
        main([str(STARTERS / "node.js.yml")])

    captured = capsys.readouterr()
    assert exited.value.code == 1
    assert captured.out == ""
    assert "Yarn only" in captured.err
