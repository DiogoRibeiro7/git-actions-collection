#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "markdown-lint calls markdownlint" {
  run_action "$REPO_ROOT/.github/actions/markdown-lint" paths=README.md
  assert_exit_code 0
  grep -q "markdownlint" "$FAKEBIN_LOG"
}

