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

@test "pr-template-enforcer checks the sections it is given, one per line" {
  PR_BODY=$'## What\nA change\n## Why\nA reason' run_action "$REPO_ROOT/.github/actions/pr-template-enforcer" \
    required-sections=$'  ## What\n  ## Why\n'
  assert_exit_code 0
}

@test "pr-template-enforcer reports every missing section" {
  PR_BODY=$'## What\nA change' run_action "$REPO_ROOT/.github/actions/pr-template-enforcer" \
    required-sections=$'## What\n## Risks\n## Rollback'
  assert_exit_code 1
  [[ "$RUN_ACTION_STDOUT" == *"Missing '## Risks'"* ]]
  [[ "$RUN_ACTION_STDOUT" == *"Missing '## Rollback'"* ]]
}

@test "pr-template-enforcer matches section text literally" {
  PR_BODY=$'## C++ notes\nSome' run_action "$REPO_ROOT/.github/actions/pr-template-enforcer" \
    required-sections='## C++ notes'
  assert_exit_code 0
}

