#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"

# The scripts run on their own: the action's install step downloads the real
# gitleaks, which test-composite-actions.yml exercises on a runner.
setup() {
  BIN="$BATS_TEST_TMPDIR/bin"
  mkdir -p "$BIN"
  export COMMAND_LOG="$BATS_TEST_TMPDIR/commands.log"
  : > "$COMMAND_LOG"
  cat > "$BIN/gitleaks" <<'EOF'
#!/usr/bin/env bash
echo "gitleaks $*" >> "$COMMAND_LOG"
exit "${GITLEAKS_EXIT:-0}"
EOF
  chmod +x "$BIN/gitleaks"
  export PATH="$BIN:$PATH"
}

@test "secret-scan redacts findings and passes the default arguments" {
  run bash "$REPO_ROOT/scripts/secret-scan/scan.sh"
  [ "$status" -eq 0 ]
  grep -qx "gitleaks detect --redact --no-git -v" "$COMMAND_LOG"
}

@test "secret-scan passes each argument, on one line or one per line" {
  INPUT_ARGS=$'--no-git --source src\n--report-path report.json' \
    run bash "$REPO_ROOT/scripts/secret-scan/scan.sh"
  [ "$status" -eq 0 ]
  grep -qx "gitleaks detect --redact --no-git --source src --report-path report.json" "$COMMAND_LOG"
}

@test "secret-scan fails when gitleaks reports a leak" {
  GITLEAKS_EXIT=1 run bash "$REPO_ROOT/scripts/secret-scan/scan.sh"
  [ "$status" -eq 1 ]
}

@test "secret-scan refuses a runner it has no gitleaks build for" {
  cat > "$BIN/uname" <<'EOF'
#!/usr/bin/env bash
case "$1" in -s) echo Darwin ;; -m) echo arm64 ;; esac
EOF
  chmod +x "$BIN/uname"
  RUNNER_TEMP="$BATS_TEST_TMPDIR" GITHUB_PATH="$BATS_TEST_TMPDIR/path" \
    run bash "$REPO_ROOT/scripts/secret-scan/install.sh"
  [ "$status" -eq 1 ]
  [[ "$output" == *"Linux x64 and arm64"* ]]
}
