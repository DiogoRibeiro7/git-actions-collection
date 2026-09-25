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


@test "setup-yarn installs Corepack on Node.js 25 and newer" {
  RUN_ACTION_WORKSPACE="$(mktemp -d)"
  touch "$RUN_ACTION_WORKSPACE/yarn.lock"
  FAKEBIN_NODE_MAJOR=26 run_action "$REPO_ROOT/.github/actions/setup-yarn" working-directory="$RUN_ACTION_WORKSPACE"
  assert_exit_code 0
  grep -q "npm install --global corepack@0.36.0" "$FAKEBIN_LOG"
}

@test "setup-yarn uses the bundled Corepack on Node.js 24" {
  RUN_ACTION_WORKSPACE="$(mktemp -d)"
  touch "$RUN_ACTION_WORKSPACE/yarn.lock"
  run_action "$REPO_ROOT/.github/actions/setup-yarn" working-directory="$RUN_ACTION_WORKSPACE"
  assert_exit_code 0
  run grep -q "npm install" "$FAKEBIN_LOG"
  [ "$status" -ne 0 ]
}
