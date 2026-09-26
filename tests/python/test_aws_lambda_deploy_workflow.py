"""aws-lambda-deploy built each runtime's package.zip in a different place, most of them
outside the workspace root the deploy step reads, passed JSON to the CLI's shorthand
--environment syntax, and raced Lambda's asynchronous updates."""

import os
from pathlib import Path

import pytest

from tests.utils.fake_runner import run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/aws-lambda-deploy.yml"
pytestmark = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")
FUNCTION_PATH = "functions/api"


def _run(tmp_path: Path, step: str, tools: dict[str, str], context: dict[str, str]):
    (tmp_path / FUNCTION_PATH).mkdir(parents=True, exist_ok=True)
    fakebin = make_fakebin(tmp_path / "tools", tools)
    return run_workflow_step(
        WORKFLOW,
        "deploy",
        step,
        context={"matrix.function.path": FUNCTION_PATH, **context},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}", "GITHUB_WORKSPACE": str(tmp_path)},
        workdir=tmp_path,
    )


@pytest.mark.parametrize(
    ("step", "tools"),
    [
        ("Build Node.js package", {"npm": "true"}),
        ("Build .NET package", {"dotnet": "mkdir -p build"}),
        ("Build Go package", {"go": "touch bootstrap"}),
    ],
)
def test_every_runtime_writes_package_zip_to_the_workspace_root(
    tmp_path: Path, step: str, tools: dict[str, str]
) -> None:
    result = _run(tmp_path, step, {**tools, "zip": 'echo "zip $*"'}, {})

    assert result.code == 0, result.stderr
    assert f"{tmp_path}/package.zip" in result.stdout


def test_java_ships_the_application_jar(tmp_path: Path) -> None:
    mvn = "mkdir -p target && echo app > target/app-1.0.jar && echo raw > target/original-app-1.0.jar"

    result = _run(tmp_path, "Build Java package", {"mvn": mvn}, {})

    assert result.code == 0, result.stderr
    assert (tmp_path / "package.zip").read_text(encoding="utf-8") == "app\n"


def test_configuration_update_sends_json_environment_then_waits(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        "Update function configuration",
        {"aws": 'printf "aws"; printf " [%s]" "$@"; echo'},
        {
            "matrix.function.name": "api",
            "matrix.function.runtime": "python3.12",
            "matrix.function.handler || ''": "app.handler",
            "matrix.function.env || ''": '{"LOG_LEVEL":"info"}',
            "matrix.function.layers || ''": "",
            "matrix.function.subnet-ids || ''": "",
            "matrix.function.security-group-ids || ''": "",
        },
    )

    assert result.code == 0, result.stderr
    assert result.stdout.splitlines() == [
        "aws [lambda] [update-function-configuration] [--function-name] [api] [--runtime] "
        '[python3.12] [--handler] [app.handler] [--environment] [{"Variables":{"LOG_LEVEL":"info"}}]',
        "aws [lambda] [wait] [function-updated-v2] [--function-name] [api]",
    ]


DEPLOY_CONTEXT = {
    "matrix.function.name": "api",
    "matrix.function.package-type || 'zip'": "zip",
    "matrix.function.image || ''": "",
    "matrix.function.s3-bucket || ''": "",
    "matrix.function.alias || ''": "prod",
}
FAKE_AWS = 'echo "aws $*" >&2; if [ "$2" = publish-version ]; then echo 7; fi'


def test_code_is_published_only_after_the_update_finished(tmp_path: Path) -> None:
    (tmp_path / "package.zip").write_text("zip", encoding="utf-8")

    result = _run(tmp_path, "Deploy function code", {"aws": FAKE_AWS}, DEPLOY_CONTEXT)

    assert result.code == 0, result.stderr
    calls = [line.split()[2] for line in result.stderr.splitlines() if line.startswith("aws ")]
    assert calls == ["update-function-code", "wait", "publish-version", "update-alias"]
    assert result.outputs["version"] == "7"


def test_a_missing_package_fails_with_a_clear_error(tmp_path: Path) -> None:
    result = _run(tmp_path, "Deploy function code", {"aws": FAKE_AWS}, DEPLOY_CONTEXT)

    assert result.code == 1
    assert "No package.zip was built for api" in result.stdout + result.stderr
