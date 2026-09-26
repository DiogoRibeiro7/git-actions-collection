#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "markdown-lint calls markdownlint" {
  run_action "$REPO_ROOT/.github/actions/markdown-lint" paths=README.md
  assert_exit_code 0
  grep -q "markdownlint" "$FAKEBIN_LOG"
}

@test "markdown-lint passes each path separately and skips node_modules" {
  run_action "$REPO_ROOT/.github/actions/markdown-lint" paths="docs README.md"
  assert_exit_code 0
  grep -qxF "markdownlint --ignore **/node_modules/** docs README.md" "$FAKEBIN_LOG"
}

@test "markdown-lint reads one path per line" {
  run_action "$REPO_ROOT/.github/actions/markdown-lint" paths=$'README.md\ndocs/\n'
  assert_exit_code 0
  grep -qxF "markdownlint --ignore **/node_modules/** README.md docs/" "$FAKEBIN_LOG"
}

@test "markdown-lint passes the config file" {
  run_action "$REPO_ROOT/.github/actions/markdown-lint" paths=README.md config-file=.markdownlint.json
  assert_exit_code 0
  grep -qxF "markdownlint --ignore **/node_modules/** -c .markdownlint.json README.md" "$FAKEBIN_LOG"
}

@test "markdown-lint fails when no Markdown file matches" {
  FAKEBIN_MARKDOWNLINT_NO_FILES=1 run_action "$REPO_ROOT/.github/actions/markdown-lint" paths=doc
  assert_exit_code 1
}

@test "markdown-lint propagates lint failures" {
  FAKEBIN_FAIL_MARKDOWNLINT=1 run_action "$REPO_ROOT/.github/actions/markdown-lint" paths=README.md
  assert_exit_code 1
}

