#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "secret-scan uses gitleaks action" {
  grep -q "gitleaks/gitleaks-action" "$REPO_ROOT/.github/actions/secret-scan/action.yml"
}
