#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/lib/action_harness.bash"

@test "check-imports missing GITHUB_OUTPUT fails" {
  RUN_ACTION_UNSET_GITHUB_OUTPUT=true run_action "$REPO_ROOT/.github/actions/check-imports" paths=src update-pyproject=false
  assert_exit_code 1
  [[ "$RUN_ACTION_STDERR" == *"GITHUB_OUTPUT is not set"* ]]
}

@test "check-imports emits JSON missing list" {
  FAKEBIN_PYTHON_MODE=check-imports run_action "$REPO_ROOT/.github/actions/check-imports" paths=src format=json update-pyproject=false
  assert_exit_code 0
  assert_output_pair missing "foo bar"
}

@test "check-imports propagates python failure" {
  FAKEBIN_FAIL_PYTHON=1 run_action "$REPO_ROOT/.github/actions/check-imports" paths=src update-pyproject=false
  assert_exit_code 1
}
