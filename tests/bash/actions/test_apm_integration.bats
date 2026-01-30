#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "apm-integration fails without provider" {
  run_action "$REPO_ROOT/.github/actions/apm-integration" api-key=token
  assert_exit_code 1
}

@test "apm-integration calls curl" {
  run_action "$REPO_ROOT/.github/actions/apm-integration" provider=datadog api-key=token deployment-id=abc
  assert_exit_code 0
  grep -q "curl" "$FAKEBIN_LOG"
}

