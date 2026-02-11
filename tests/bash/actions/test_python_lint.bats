#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "python-lint calls ruff" {
  run_action "$REPO_ROOT/.github/actions/python-lint" enable-mypy=false
  assert_exit_code 0
  grep -q "ruff" "$FAKEBIN_LOG"
}

@test "python-lint calls mypy when enabled" {
  run_action "$REPO_ROOT/.github/actions/python-lint" enable-mypy=true
  assert_exit_code 0
  grep -q "mypy" "$FAKEBIN_LOG"
}

