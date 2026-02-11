#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "smart-dependency-update fails without manifests" {
  run_action "$REPO_ROOT/.github/actions/smart-dependency-update" manifests=
  assert_exit_code 1
}

@test "smart-dependency-update calls python" {
  FAKEBIN_PYTHON_MODE=smart-update run_action "$REPO_ROOT/.github/actions/smart-dependency-update" manifests=pyproject.toml
  assert_exit_code 0
  grep -q "python" "$FAKEBIN_LOG"
}

