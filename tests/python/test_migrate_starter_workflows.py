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
from scripts.interface_snapshot import workflow_interface
from scripts.migrate_starter_workflows import main

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "workflows"
STARTERS = FIXTURES / "github-starters"
MIGRATED = ["python-package", "node.js", "go", "maven", "gradle", "ruby", "dotnet", "rust", "deno"]
NOT_MIGRATED = {"r": "R CMD check"}


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


def test_github_node_starter_notes_the_scripts_node_ci_needs_and_the_build():
    plan = _plan(_read(STARTERS / "node.js.yml"))

    assert plan.inputs["package-manager"] == "npm"
    assert any("`npm run lint` and `npm run test`" in note for note in plan.notes)
    assert any("`npm run build --if-present`" in note for note in plan.notes)


def _node_starter(*steps: str) -> str:
    return (
        "on: push\njobs:\n  b:\n    runs-on: ubuntu-latest\n    steps:\n"
        + "".join(f"      - {step}\n" for step in steps)
    )


def test_the_package_manager_comes_from_the_cache_the_pnpm_action_or_the_commands():
    yarn = _plan(
        _node_starter("uses: actions/setup-node@v4\n        with:\n          cache: yarn")
    )
    pnpm = _plan(
        _node_starter("uses: pnpm/action-setup@v4", "uses: actions/setup-node@v4", "run: pnpm test")
    )
    npm = _plan(_read(FIXTURES / "starter_node.yml"))

    assert yarn.inputs["package-manager"] == "yarn"
    assert pnpm.inputs["package-manager"] == "pnpm"
    assert npm.inputs["package-manager"] == "npm"
    assert any("Corepack" in note for note in pnpm.notes)
    assert not any("Not carried over" in note for note in pnpm.notes + npm.notes)


def test_without_a_package_manager_node_ci_detects_it():
    plan = _plan(_node_starter("uses: actions/setup-node@v4", "run: node test.js"))

    assert plan.uses and "node-ci.yml@v1" in plan.uses
    assert "package-manager" not in plan.inputs
    assert any("packageManager field or the lockfile" in note for note in plan.notes)
    assert any("`node test.js`" in note for note in plan.notes)


def test_only_what_node_ci_runs_is_carried_over():
    plan = _plan(
        _node_starter(
            "uses: actions/setup-node@v4",
            "run: npm install --no-audit",
            "run: npm run lint",
            "run: npm test",
            "run: npm test -- --coverage",
            "run: npm run build",
        )
    )

    (note,) = [note for note in plan.notes if note.startswith("Not carried over")]
    assert note.endswith(": `npm test -- --coverage`, `npm run build`.")


def test_a_bun_starter_is_not_migrated():
    content = _node_starter("uses: actions/setup-node@v4", "run: bun install", "run: bun test")
    plan = _plan(content)

    assert plan.ecosystem == "node"
    assert plan.workflow is None and plan.uses is None
    assert "uses bun" in explain(plan)
    with pytest.raises(SystemExit, match="npm, Yarn or pnpm"):
        convert(content)


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


def _bun_starter(tmp_path: Path) -> Path:
    starter = tmp_path / "bun.yml"
    starter.write_text(
        _node_starter("uses: actions/setup-node@v4", "run: bun install", "run: bun test"),
        encoding="utf-8",
    )
    return starter


def test_cli_reports_a_starter_it_cannot_migrate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    with pytest.raises(SystemExit) as exited:
        main([str(_bun_starter(tmp_path)), "--json"])

    report = json.loads(capsys.readouterr().out)
    assert exited.value.code == 1
    assert report["workflow"] is None and report["migrated"] is None
    assert any("uses bun" in note for note in report["notes"])


def test_cli_explains_a_starter_it_cannot_migrate_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    with pytest.raises(SystemExit) as exited:
        main([str(_bun_starter(tmp_path))])

    captured = capsys.readouterr()
    assert exited.value.code == 1
    assert captured.out == ""
    assert "uses bun" in captured.err


@pytest.mark.parametrize("starter", MIGRATED)
def test_github_starters_migrate_to_the_expected_workflow(starter: str):
    migrated = convert(_read(STARTERS / f"{starter}.yml"))

    assert yaml.safe_load(migrated) == yaml.safe_load(_read(STARTERS / f"{starter}.migrated.yml"))


@pytest.mark.parametrize(("starter", "reason"), NOT_MIGRATED.items())
def test_github_starters_without_a_reusable_workflow(starter: str, reason: str):
    plan = _plan(_read(STARTERS / f"{starter}.yml"))

    assert plan.workflow is None
    assert reason in explain(plan)


@pytest.mark.parametrize("starter", MIGRATED)
def test_plans_use_only_what_the_target_workflow_declares(starter: str):
    """The tool hard-codes each target's inputs and permissions; keep them in step."""
    plan = _plan(_read(STARTERS / f"{starter}.yml"))
    interface = workflow_interface(ROOT, plan.workflow)

    assert set(plan.inputs) <= set(interface["inputs"])
    assert plan.permissions == interface["permissions"]


def _java(steps: str, java_version: str = "17") -> str:
    return (
        "on: push\njobs:\n  b:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/setup-java@v4\n"
        f"        with:\n          java-version: '{java_version}'\n"
        "          distribution: temurin\n"
        + steps
    )


@pytest.mark.parametrize(
    ("steps", "tool"),
    [
        ("      - run: mvn -B verify\n", "maven"),
        ("      - run: ./mvnw -B verify\n", "maven"),
        ("      - uses: gradle/actions/setup-gradle@v4\n      - run: ./gradlew check\n", "gradle"),
        ("      - run: gradle build\n", "gradle"),
    ],
)
def test_java_build_tool_is_detected(steps: str, tool: str):
    assert _plan(_java(steps)).inputs["build-tool"] == tool


def test_unknown_java_build_tool_keeps_the_default_and_says_so():
    plan = _plan(_java("      - run: make\n"))

    assert "build-tool" not in plan.inputs
    assert any("Could not tell Maven from Gradle" in note for note in plan.notes)


def test_java_version_other_than_17_is_noted():
    plan = _plan(_java("      - run: mvn -B test\n", java_version="21"))

    assert any("Temurin JDK 17; the starter asked for 21" in note for note in plan.notes)


def test_dotnet_frameworks_follow_the_sdk_versions():
    plan = _plan(
        "on: push\njobs:\n  b:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/setup-dotnet@v4\n"
        "        with:\n          dotnet-version: |\n            8.0.x\n            9.0.x\n"
    )

    assert plan.inputs["dotnet-version"] == "9.0.x"
    assert plan.inputs["frameworks"] == '["net8.0", "net9.0"]'


@pytest.mark.parametrize(
    ("setup", "toolchain"),
    [
        ("      - uses: dtolnay/rust-toolchain@stable\n", "stable"),
        ("      - uses: dtolnay/rust-toolchain@1.85.0\n", "1.85.0"),
        (
            "      - uses: dtolnay/rust-toolchain@" + "a" * 40 + "\n"
            "        with:\n          toolchain: nightly\n",
            "nightly",
        ),
        (
            "      - uses: actions-rs/toolchain@v1\n        with:\n          toolchain: beta\n",
            "beta",
        ),
    ],
)
def test_rust_toolchain_is_carried_over(setup: str, toolchain: str):
    plan = _plan(
        "on: push\njobs:\n  b:\n    runs-on: ubuntu-latest\n    steps:\n"
        + setup
        + "      - run: cargo test\n"
    )

    assert plan.inputs == {"rust-toolchain": toolchain}


def test_rust_is_detected_from_cargo_commands_alone():
    plan = _plan(_read(STARTERS / "rust.yml"))

    assert plan.ecosystem == "rust" and plan.workflow == "rust-ci.yml"
    assert "rust-toolchain" not in plan.inputs


def test_deno_test_flags_are_noted():
    plan = _plan(_read(STARTERS / "deno.yml"))

    assert any("`deno test -A`" in note for note in plan.notes)


def test_bun_is_detected_but_not_migrated():
    plan = _plan(
        "on: push\njobs:\n  b:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: oven-sh/setup-bun@v2\n      - run: bun test\n"
    )

    assert plan.ecosystem == "node" and plan.workflow is None
    assert "Bun" in explain(plan)
