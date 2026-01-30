#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/lib/action_harness.bash"

@test "smart-dependency-update requires manifests" {
  run_action "$REPO_ROOT/.github/actions/smart-dependency-update" manifests=
  assert_exit_code 1
}

@test "smart-dependency-update writes report output" {
  FAKEBIN_PYTHON_MODE=smart-update run_action "$REPO_ROOT/.github/actions/smart-dependency-update" manifests=pyproject.toml
  assert_exit_code 0
  assert_output_pair report "{}"
}

@test "smart-dependency-update propagates python failure" {
  FAKEBIN_FAIL_PYTHON=1 run_action "$REPO_ROOT/.github/actions/smart-dependency-update" manifests=pyproject.toml
  assert_exit_code 1
}
