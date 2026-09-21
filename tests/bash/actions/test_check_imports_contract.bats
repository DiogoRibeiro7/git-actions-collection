#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "check-imports fails when GITHUB_OUTPUT missing" {
  GITHUB_OUTPUT="" run_action "$REPO_ROOT/.github/actions/check-imports" paths=src update-pyproject=false
  assert_exit_code 1
}

@test "check-imports calls python" {
  FAKEBIN_PYTHON_MODE=check-imports run_action "$REPO_ROOT/.github/actions/check-imports" paths=src update-pyproject=false
  assert_exit_code 0
  grep -q "python" "$FAKEBIN_LOG"
}

