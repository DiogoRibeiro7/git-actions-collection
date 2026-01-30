#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "setup-r calls Rscript when packages provided" {
  run_action "$REPO_ROOT/.github/actions/setup-r" packages=lintr
  assert_exit_code 0
  grep -q "Rscript" "$FAKEBIN_LOG"
}

