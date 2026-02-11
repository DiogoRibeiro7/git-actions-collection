#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "pr-template-enforcer fails on empty body" {
  run_action "$REPO_ROOT/.github/actions/pr-template-enforcer" 
  assert_exit_code 1
}

@test "pr-template-enforcer succeeds with required sections" {
  PR_BODY="## Summary\nDone\n## Testing\nN/A" run_action "$REPO_ROOT/.github/actions/pr-template-enforcer"
  assert_exit_code 0
}

