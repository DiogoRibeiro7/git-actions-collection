import os
from pathlib import Path

import pytest

from tests.utils.fake_runner import run_action
from tests.utils.fakebin import make_fakebin

REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIONS_DIR = REPO_ROOT / ".github" / "actions"


pytestmark = pytest.mark.skipif(os.name != "posix", reason="Fake runner requires bash (Linux CI)")


def _env_with_path(fakebin: Path) -> dict[str, str]:
    return {"PATH": f"{fakebin}:{os.environ.get('PATH','')}"}


def test_aws_lambda_build_happy(tmp_path: Path):
    fakebin = make_fakebin(
        tmp_path,
        {
            "python": 'echo "python $@"',
            "pip": 'echo "pip $@"',
            "rsync": 'echo "rsync $@"',
            "zip": 'mkdir -p "$(dirname \"$2\")"; touch "$2"; echo "zip $@"',
        },
    )
    src = tmp_path / "lambda"
    src.mkdir()
    (src / "requirements.txt").write_text("")

    result = run_action(
        ACTIONS_DIR / "aws-lambda-build",
        inputs={"src": str(src), "output-zip": "artifact/lambda.zip", "pip-version": "23.0.1"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )

    assert result.code == 0
    assert (tmp_path / "artifact" / "lambda.zip").exists()
    assert "Created artifact/lambda.zip" in result.stdout


def test_aws_lambda_build_invalid_src(tmp_path: Path):
    result = run_action(
        ACTIONS_DIR / "aws-lambda-build",
        inputs={"src": "", "output-zip": "artifact/lambda.zip"},
        workdir=tmp_path,
    )
    assert result.code != 0
    assert "src input must not be empty" in result.stderr


def test_aws_lambda_build_latest_pip(tmp_path: Path):
    fakebin = make_fakebin(
        tmp_path,
        {
            "python": 'echo "python $@"',
            "pip": 'echo "pip $@"',
            "rsync": 'echo "rsync $@"',
            "zip": 'mkdir -p "$(dirname \"$2\")"; touch "$2";',
        },
    )
    src = tmp_path / "lambda"
    src.mkdir()

    result = run_action(
        ACTIONS_DIR / "aws-lambda-build",
        inputs={"src": str(src), "output-zip": "artifact/lambda.zip", "pip-version": "latest"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "python -m pip install --upgrade pip" in result.stdout


def test_check_imports_happy(tmp_path: Path):
    fakebin = make_fakebin(
        tmp_path,
        {
            "python": 'if [ "$1" = "-c" ]; then echo "foo bar"; exit 0; fi; '
            'if echo "$@" | grep -q "--format json"; then '
            'echo "{\\"missing\\":[\\"foo\\",\\"bar\\"]}"; exit 0; fi; '
            'echo "checked"; exit 0',
            "pip": 'echo "pip $@"',
        },
    )

    result = run_action(
        ACTIONS_DIR / "check-imports",
        inputs={"paths": "src", "update-pyproject": "false", "format": "json"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )

    assert result.code == 0
    assert result.outputs.get("missing") == "foo bar"


def test_check_imports_missing_github_output(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"python": 'exit 0', "pip": 'echo pip'})
    result = run_action(
        ACTIONS_DIR / "check-imports",
        inputs={"paths": "src", "update-pyproject": "false"},
        env={**_env_with_path(fakebin), "GITHUB_OUTPUT": ""},
        workdir=tmp_path,
    )
    assert result.code != 0
    assert "GITHUB_OUTPUT is not set" in result.stderr


def test_check_imports_update_step_runs(tmp_path: Path):
    fakebin = make_fakebin(
        tmp_path,
        {
            "python": 'if echo "$@" | grep -q "--format json"; then '
            'echo "{\\"missing\\":[\\"pkg\\"]}"; exit 0; fi; '
            'if echo "$@" | grep -q "--update"; then echo "updated"; fi; exit 0',
            "pip": 'echo "pip $@"',
        },
    )

    result = run_action(
        ACTIONS_DIR / "check-imports",
        inputs={"paths": "src", "update-pyproject": "true", "smart-update": "false"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )

    assert result.code == 0
    assert "updated" in result.stdout


def test_benchmark_smoke_happy(tmp_path: Path):
    fakebin = make_fakebin(
        tmp_path,
        {
            "python": 'echo "python $@"',
            "pip": 'echo "pip $@"',
            "pytest": 'echo "pytest $@"',
        },
    )

    result = run_action(
        ACTIONS_DIR / "benchmark-smoke",
        inputs={"pytest-args": "-k fast", "pip-version": "24.3.1"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "pytest -k fast --benchmark-only --benchmark-json=benchmark.json" in result.stdout


def test_benchmark_smoke_pytest_failure(tmp_path: Path):
    fakebin = make_fakebin(
        tmp_path,
        {"python": 'echo "python $@"', "pip": 'echo "pip $@"', "pytest": 'exit 2'},
    )
    result = run_action(
        ACTIONS_DIR / "benchmark-smoke",
        inputs={"pytest-args": "-k fast"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert result.code == 2


def test_benchmark_smoke_pip_latest(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"python": 'echo "python $@"', "pip": 'echo "pip $@"', "pytest": 'exit 0'})
    result = run_action(
        ACTIONS_DIR / "benchmark-smoke",
        inputs={"pip-version": "latest"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "python -m pip install --upgrade pip" in result.stdout


def test_apm_integration_datadog(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"curl": 'echo "curl $@"', "jq": 'echo ""'})
    result = run_action(
        ACTIONS_DIR / "apm-integration",
        inputs={"provider": "datadog", "api-key": "token", "deployment-id": "abc"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert result.code == 0
    assert "https://api.datadoghq.com/api/v1/events" in result.stdout


def test_apm_integration_invalid_provider(tmp_path: Path):
    result = run_action(
        ACTIONS_DIR / "apm-integration",
        inputs={"provider": "bad", "api-key": "token"},
        workdir=tmp_path,
    )
    assert result.code != 0
    assert "Unsupported provider" in result.stderr


def test_apm_integration_metrics_warning(tmp_path: Path):
    metrics = REPO_ROOT / "tests" / "bash" / "fixtures" / "metrics.json"
    fakebin = make_fakebin(
        tmp_path,
        {
            "curl": 'echo "curl $@"',
            "jq": 'if [ "$2" = ".latency // empty" ]; then echo 200; else echo 100; fi',
        },
    )
    result = run_action(
        ACTIONS_DIR / "apm-integration",
        inputs={
            "provider": "datadog",
            "api-key": "token",
            "deployment-id": "abc",
            "metrics-file": str(metrics),
        },
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "latency 200 exceeded threshold 100" in result.stdout


def test_r_lint_package_inputs(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"Rscript": 'echo "Rscript $@"'})
    result = run_action(
        ACTIONS_DIR / "r-lint",
        inputs={"additional-packages": "testthat"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert result.outputs.get("packages") == "lintr,testthat"


def test_r_lint_missing_github_output(tmp_path: Path):
    result = run_action(
        ACTIONS_DIR / "r-lint",
        inputs={"additional-packages": "testthat"},
        env={"GITHUB_OUTPUT": ""},
        workdir=tmp_path,
    )
    assert result.code != 0


def test_r_lint_run_calls_rscript(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"Rscript": 'echo "Rscript $@"'})
    result = run_action(
        ACTIONS_DIR / "r-lint",
        inputs={"targets": "R", "config-file": ".lintr"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "Rscript" in result.stdout


def test_smart_dependency_update_report(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"python": 'echo "{}"', "pip": 'echo "pip $@"'})
    result = run_action(
        ACTIONS_DIR / "smart-dependency-update",
        inputs={"manifests": "pyproject.toml"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert result.outputs.get("report") == "{}"


def test_smart_dependency_update_missing_manifests(tmp_path: Path):
    result = run_action(
        ACTIONS_DIR / "smart-dependency-update",
        inputs={"manifests": ""},
        workdir=tmp_path,
    )
    assert result.code != 0


def test_smart_dependency_update_flags(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"python": 'echo "python $@"', "pip": 'echo "pip $@"'})
    result = run_action(
        ACTIONS_DIR / "smart-dependency-update",
        inputs={
            "manifests": "pyproject.toml",
            "apply": "true",
            "dependabot": "true",
            "repo": "acme/demo",
            "batch-size": "7",
        },
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "--apply" in result.stdout
    assert "--dependabot" in result.stdout
    assert "--repo acme/demo" in result.stdout


def test_python_type_check_happy(tmp_path: Path):
    fakebin = make_fakebin(
        tmp_path,
        {
            "python": 'echo "python $@"',
            "mypy": 'echo "mypy $@"',
        },
    )
    result = run_action(
        ACTIONS_DIR / "python-type-check",
        inputs={"requirements-file": "req.txt", "mypy-args": "src"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "python -m pip install -r req.txt" in result.stdout
    assert "mypy src" in result.stdout


def test_python_type_check_mypy_failure(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"python": 'echo "python $@"', "mypy": 'exit 5'})
    result = run_action(
        ACTIONS_DIR / "python-type-check",
        inputs={"mypy-args": "src"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert result.code == 5


def test_python_type_check_default_pip(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"python": 'echo "python $@"', "mypy": 'exit 0'})
    result = run_action(
        ACTIONS_DIR / "python-type-check",
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "pip==24.3.1" in result.stdout


def test_pr_template_enforcer_happy(tmp_path: Path):
    body = "## Summary\nDone\n## Testing\nN/A"
    result = run_action(
        ACTIONS_DIR / "pr-template-enforcer",
        env={"PR_BODY": body},
        workdir=tmp_path,
    )
    assert result.code == 0


def test_pr_template_enforcer_missing_section(tmp_path: Path):
    body = "## Summary\nOnly summary"
    result = run_action(
        ACTIONS_DIR / "pr-template-enforcer",
        env={"PR_BODY": body},
        workdir=tmp_path,
    )
    assert result.code != 0


def test_pr_template_enforcer_empty(tmp_path: Path):
    result = run_action(
        ACTIONS_DIR / "pr-template-enforcer",
        env={"PR_BODY": ""},
        workdir=tmp_path,
    )
    assert result.code != 0


def test_gradle_build_happy(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    gradlew = project / "gradlew"
    gradlew.write_text("#!/usr/bin/env bash\necho gradlew $@\n")
    os.chmod(gradlew, 0o755)

    result = run_action(
        ACTIONS_DIR / "gradle-build",
        inputs={"tasks": "build", "gradle-args": "--info", "working-directory": str(project)},
        workdir=tmp_path,
    )
    assert "gradlew build --info" in result.stdout


def test_gradle_build_empty_tasks(tmp_path: Path):
    result = run_action(
        ACTIONS_DIR / "gradle-build",
        inputs={"tasks": ""},
        workdir=tmp_path,
    )
    assert result.code != 0


def test_gradle_build_gradlew_failure(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    gradlew = project / "gradlew"
    gradlew.write_text("#!/usr/bin/env bash\nexit 3\n")
    os.chmod(gradlew, 0o755)

    result = run_action(
        ACTIONS_DIR / "gradle-build",
        inputs={"tasks": "build", "working-directory": str(project)},
        workdir=tmp_path,
    )
    assert result.code == 3


def test_python_lint_happy(tmp_path: Path):
    fakebin = make_fakebin(
        tmp_path,
        {
            "python": 'echo "python $@"',
            "pip": 'echo "pip $@"',
            "ruff": 'echo "ruff $@"',
            "mypy": 'echo "mypy $@"',
        },
    )
    result = run_action(
        ACTIONS_DIR / "python-lint",
        inputs={"enable-mypy": "true"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "ruff check ." in result.stdout
    assert "mypy ." in result.stdout


def test_python_lint_ruff_failure(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"python": 'echo "python $@"', "pip": 'echo "pip $@"', "ruff": 'exit 4'})
    result = run_action(
        ACTIONS_DIR / "python-lint",
        inputs={"enable-mypy": "false"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert result.code == 4


def test_python_lint_no_mypy(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"python": 'echo "python $@"', "pip": 'echo "pip $@"', "ruff": 'echo "ruff $@"'})
    result = run_action(
        ACTIONS_DIR / "python-lint",
        inputs={"enable-mypy": "false"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "mypy" not in result.stdout


def test_markdown_lint_with_config(tmp_path: Path):
    fakebin = make_fakebin(
        tmp_path,
        {
            "npm": 'echo "npm $@"',
            "markdownlint": 'echo "markdownlint $@"',
        },
    )
    result = run_action(
        ACTIONS_DIR / "markdown-lint",
        inputs={"paths": "README.md", "config-file": ".markdownlint.yml"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "markdownlint -c .markdownlint.yml README.md" in result.stdout


def test_markdown_lint_failure(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"npm": 'echo "npm $@"', "markdownlint": 'exit 7'})
    result = run_action(
        ACTIONS_DIR / "markdown-lint",
        inputs={"paths": "README.md"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert result.code == 7


def test_markdown_lint_default(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"npm": 'echo "npm $@"', "markdownlint": 'echo "markdownlint $@"'})
    result = run_action(
        ACTIONS_DIR / "markdown-lint",
        inputs={"paths": "README.md"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "markdownlint README.md" in result.stdout


def test_setup_poetry_install(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"python": 'echo "python $@"', "pip": 'echo "pip $@"'})
    result = run_action(
        ACTIONS_DIR / "setup-poetry",
        inputs={"install-deps": "false", "pip-version": "24.0.0"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "pip==24.0.0" in result.stdout


def test_setup_poetry_configure_cache(tmp_path: Path):
    env_file = tmp_path / "envfile"
    fakebin = make_fakebin(tmp_path, {"python": 'echo "python $@"', "pip": 'echo "pip $@"'})
    result = run_action(
        ACTIONS_DIR / "setup-poetry",
        inputs={"install-deps": "false"},
        env={**_env_with_path(fakebin), "GITHUB_ENV": str(env_file)},
        workdir=tmp_path,
    )
    assert result.code == 0
    assert "POETRY_CACHE_DIR" in env_file.read_text()


def test_setup_poetry_missing_github_env(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"python": 'echo "python $@"', "pip": 'echo "pip $@"'})
    result = run_action(
        ACTIONS_DIR / "setup-poetry",
        inputs={"install-deps": "false"},
        env={**_env_with_path(fakebin), "GITHUB_ENV": ""},
        workdir=tmp_path,
    )
    assert result.code != 0


def test_setup_yarn_happy(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "yarn.lock").write_text("")
    fakebin = make_fakebin(tmp_path, {"corepack": 'echo "corepack $@"', "yarn": 'echo "yarn $@"'})
    result = run_action(
        ACTIONS_DIR / "setup-yarn",
        inputs={"working-directory": str(project)},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "corepack enable" in result.stdout
    assert "yarn install --immutable" in result.stdout


def test_setup_yarn_no_lockfile(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    fakebin = make_fakebin(tmp_path, {"corepack": 'echo "corepack $@"', "yarn": 'echo "yarn $@"'})
    result = run_action(
        ACTIONS_DIR / "setup-yarn",
        inputs={"working-directory": str(project)},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "No yarn.lock found" in result.stdout


def test_setup_yarn_yarn_failure(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "yarn.lock").write_text("")
    fakebin = make_fakebin(tmp_path, {"corepack": 'echo "corepack $@"', "yarn": 'exit 9'})
    result = run_action(
        ACTIONS_DIR / "setup-yarn",
        inputs={"working-directory": str(project)},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert result.code == 9


def test_setup_r_with_packages(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"Rscript": 'echo "Rscript $@"'})
    result = run_action(
        ACTIONS_DIR / "setup-r",
        inputs={"packages": "lintr"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "Rscript" in result.stdout


def test_setup_r_no_packages(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"Rscript": 'echo "Rscript $@"'})
    result = run_action(
        ACTIONS_DIR / "setup-r",
        inputs={"packages": ""},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert "Rscript" not in result.stdout


def test_setup_r_rscript_failure(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"Rscript": 'exit 6'})
    result = run_action(
        ACTIONS_DIR / "setup-r",
        inputs={"packages": "lintr"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert result.code == 6


def test_r_testthat_happy(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"Rscript": 'echo "Rscript $@"'})
    result = run_action(
        ACTIONS_DIR / "r-testthat",
        inputs={"use-devtools": "true", "install-dependencies": "false"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert result.outputs.get("packages") == "remotes,testthat,devtools"
    assert "Rscript" in result.stdout


def test_r_testthat_missing_github_output(tmp_path: Path):
    result = run_action(
        ACTIONS_DIR / "r-testthat",
        inputs={"use-devtools": "true"},
        env={"GITHUB_OUTPUT": ""},
        workdir=tmp_path,
    )
    assert result.code != 0


def test_r_testthat_rscript_failure(tmp_path: Path):
    fakebin = make_fakebin(tmp_path, {"Rscript": 'exit 8'})
    result = run_action(
        ACTIONS_DIR / "r-testthat",
        inputs={"install-dependencies": "false"},
        env=_env_with_path(fakebin),
        workdir=tmp_path,
    )
    assert result.code == 8


def test_secret_scan_default(tmp_path: Path):
    result = run_action(
        ACTIONS_DIR / "secret-scan",
        workdir=tmp_path,
    )
    assert result.code == 0


def test_secret_scan_args_input(tmp_path: Path):
    result = run_action(
        ACTIONS_DIR / "secret-scan",
        inputs={"args": "--no-git"},
        workdir=tmp_path,
    )
    assert result.code == 0


def test_secret_scan_outputs_empty(tmp_path: Path):
    result = run_action(
        ACTIONS_DIR / "secret-scan",
        workdir=tmp_path,
    )
    assert result.outputs == {}
