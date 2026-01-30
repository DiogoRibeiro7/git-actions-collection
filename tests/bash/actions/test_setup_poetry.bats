#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "setup-poetry installs via pip" {
  run_action "$REPO_ROOT/.github/actions/setup-poetry" install-deps=false
  assert_exit_code 0
  grep -q "pip" "$FAKEBIN_LOG"
}

@test "setup-poetry writes cache env" {
  run_action "$REPO_ROOT/.github/actions/setup-poetry" install-deps=false
  assert_exit_code 0
  grep -q "POETRY_CACHE_DIR" "$GITHUB_ENV"
}

