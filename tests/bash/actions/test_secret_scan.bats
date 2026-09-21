#!/usr/bin/env bash
set -euo pipefail

@test "secret-scan uses gitleaks action" {
  grep -q "gitleaks/gitleaks-action" "$REPO_ROOT/.github/actions/secret-scan/action.yml"
}

