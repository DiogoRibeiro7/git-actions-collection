"""Regression tests for the runner behaviors our action tests depend on."""

import os

import pytest
import yaml

from tests.utils.fake_runner import run_action

pytestmark = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")


def action(tmp_path, steps, **metadata):
    path = tmp_path / "collection" / "action.yml"
    path.parent.mkdir()
    path.write_text(yaml.safe_dump({"runs": {"using": "composite", "steps": steps}, **metadata}))
    return path


def shell(command, **metadata):
    return {"shell": "bash", "run": command, **metadata}


def test_only_declared_outputs_are_exposed_and_steps_are_isolated(tmp_path):
    path = action(
        tmp_path,
        [
            shell('echo "value=first" >> "$GITHUB_OUTPUT"', id="first"),
            shell('echo "private=second" >> "$GITHUB_OUTPUT"', id="second"),
        ],
        outputs={"public": {"value": "${{ steps.first.outputs.value }}"}},
    )
    result = run_action(path)
    assert result.outputs == {"public": "first"}
    assert result.step_outputs == {"first": {"value": "first"}, "second": {"private": "second"}}


def test_environment_and_multiline_outputs_reach_later_steps(tmp_path):
    path = action(
        tmp_path,
        [
            shell('printf "MESSAGE<<EOF\\nhello\\nworld\\nEOF\\n" >> "$GITHUB_ENV"'),
            shell('printf "text<<EOF\\n%s\\nEOF\\n" "$MESSAGE" >> "$GITHUB_OUTPUT"', id="emit"),
        ],
        outputs={"message": {"value": "${{ steps.emit.outputs.text }}"}},
    )
    result = run_action(path)
    assert result.outputs == {"message": "hello\nworld"}


@pytest.mark.parametrize(
    "condition", ["inputs.enabled == 'true'", "${{ inputs.enabled == 'true' }}", False]
)
def test_false_conditions_skip_shell_steps(tmp_path, condition):
    path = action(
        tmp_path,
        [
            shell("exit 97", **{"if": condition}),
            shell("echo executed"),
        ],
        inputs={"enabled": {"default": "false"}},
    )
    result = run_action(path)
    assert result.code == 0
    assert result.stdout == "executed\n"


@pytest.mark.parametrize(
    "command", ["false\necho hidden failure", "false | cat\necho hidden failure"]
)
def test_shell_failures_stop_the_action(tmp_path, command):
    path = action(tmp_path, [shell(command), shell("echo should not run")])
    result = run_action(path)
    assert result.code != 0
    assert result.stdout == ""


def test_skipped_external_actions_are_reported(tmp_path):
    path = action(tmp_path, [{"uses": "example/setup@v1"}, shell("echo tested")])
    result = run_action(path)
    assert result.skipped_uses == ("example/setup@v1",)
    assert result.stdout == "tested\n"


def test_external_only_action_cannot_pass_as_a_behavioral_test(tmp_path):
    path = action(tmp_path, [{"uses": "example/setup@v1"}])
    with pytest.raises(ValueError, match="No shell steps executed"):
        run_action(path)


@pytest.mark.parametrize(
    "step",
    [
        shell("echo '${{ runner.os }}'"),
        shell("echo \"${{ steps.example.outputs.value || 'fallback' }}\""),
        shell("echo unsupported", **{"if": "contains(inputs.enabled, 'true')"}),
        {"shell": "pwsh", "run": "Write-Output unsupported"},
    ],
)
def test_unsupported_features_fail_explicitly(tmp_path, step):
    path = action(tmp_path, [step])
    with pytest.raises(ValueError, match="Unsupported"):
        run_action(path)


def test_composite_inputs_require_explicit_environment_mapping(tmp_path, monkeypatch):
    monkeypatch.delenv("INPUT_MESSAGE", raising=False)
    path = action(
        tmp_path,
        [shell('test -z "${INPUT_MESSAGE+x}"')],
        inputs={"message": {"default": "not automatically exported"}},
    )
    assert run_action(path).code == 0


def test_helpers_are_not_silently_resolved_in_the_collection(tmp_path):
    path = action(tmp_path, [shell("bash scripts/helper.sh")])
    scripts = path.parent / "scripts"
    scripts.mkdir()
    (scripts / "helper.sh").write_text("echo incorrectly resolved\n")
    workspace = tmp_path / "consumer"
    result = run_action(path, workdir=workspace)
    assert result.code != 0
    assert "incorrectly resolved" not in result.stdout


def test_missing_working_directory_is_not_created(tmp_path):
    path = action(tmp_path, [shell("echo hidden mistake", **{"working-directory": "missing"})])
    with pytest.raises(FileNotFoundError):
        run_action(path)
