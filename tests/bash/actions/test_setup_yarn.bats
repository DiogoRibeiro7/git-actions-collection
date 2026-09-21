#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "setup-yarn runs corepack" {
  RUN_ACTION_WORKSPACE="$(mktemp -d)"
  touch "$RUN_ACTION_WORKSPACE/yarn.lock"
  run_action "$REPO_ROOT/.github/actions/setup-yarn" working-directory="$RUN_ACTION_WORKSPACE"
  assert_exit_code 0
  grep -q "corepack" "$FAKEBIN_LOG"
}

@test "setup-yarn runs yarn install" {
  RUN_ACTION_WORKSPACE="$(mktemp -d)"
  touch "$RUN_ACTION_WORKSPACE/yarn.lock"
  run_action "$REPO_ROOT/.github/actions/setup-yarn" working-directory="$RUN_ACTION_WORKSPACE"
  assert_exit_code 0
  grep -q "yarn install" "$FAKEBIN_LOG"
}

