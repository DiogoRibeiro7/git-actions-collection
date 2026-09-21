#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/lib/action_harness.bash"

@test "run_action sets inputs and captures outputs" {
  FAKEBIN_PYTHON_MODE=check-imports run_action "$REPO_ROOT/.github/actions/check-imports" paths=src update-pyproject=false
  assert_exit_code 0
  [ -f "$GITHUB_OUTPUT" ]
}

@test "run_action captures stderr on failure" {
  run_action "$REPO_ROOT/.github/actions/apm-integration" provider=bad api-key=token
  assert_exit_code 1
  [[ "$RUN_ACTION_STDERR" == *"Unsupported provider"* ]]
}

@test "run_action writes outputs when script echoes to GITHUB_OUTPUT" {
  run_action "$REPO_ROOT/.github/actions/r-lint" additional-packages=testthat
  assert_exit_code 0
  assert_output_pair packages "lintr,testthat"
}
