#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "r-testthat writes packages output" {
  run_action "$REPO_ROOT/.github/actions/r-testthat" use-devtools=true
  assert_exit_code 0
  assert_output_pair packages "remotes,testthat,devtools"
}

@test "r-testthat calls Rscript" {
  run_action "$REPO_ROOT/.github/actions/r-testthat" install-dependencies=false
  assert_exit_code 0
  grep -q "Rscript" "$FAKEBIN_LOG"
}

