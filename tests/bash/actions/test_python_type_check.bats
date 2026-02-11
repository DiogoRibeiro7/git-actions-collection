#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "python-type-check calls mypy" {
  run_action "$REPO_ROOT/.github/actions/python-type-check" mypy-args=src
  assert_exit_code 0
  grep -q "mypy" "$FAKEBIN_LOG"
}

