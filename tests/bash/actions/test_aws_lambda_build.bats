#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "aws-lambda-build fails without src" {
  run_action "$REPO_ROOT/.github/actions/aws-lambda-build" src= output-zip=artifact/lambda.zip
  assert_exit_code 1
}

@test "aws-lambda-build calls rsync and zip" {
  run_action "$REPO_ROOT/.github/actions/aws-lambda-build" src=missing output-zip=artifact/lambda.zip
  assert_exit_code 0
  grep -q "rsync" "$FAKEBIN_LOG"
  grep -q "zip" "$FAKEBIN_LOG"
}

