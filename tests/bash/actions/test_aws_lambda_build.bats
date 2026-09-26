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

@test "aws-lambda-build writes the archive to any output directory" {
  run_action "$REPO_ROOT/.github/actions/aws-lambda-build" src=missing output-zip=dist/fn.zip
  assert_exit_code 0
  [ -d "$GITHUB_WORKSPACE/dist" ]
  grep -qx "zip -r $GITHUB_WORKSPACE/dist/fn.zip ." "$FAKEBIN_LOG"
}

