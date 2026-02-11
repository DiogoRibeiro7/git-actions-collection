#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "r-lint writes packages output" {
  run_action "$REPO_ROOT/.github/actions/r-lint" additional-packages=testthat
  assert_exit_code 0
  assert_output_pair packages "lintr,testthat"
}

@test "r-lint calls Rscript" {
  run_action "$REPO_ROOT/.github/actions/r-lint" targets=R
  assert_exit_code 0
  grep -q "Rscript" "$FAKEBIN_LOG"
}

