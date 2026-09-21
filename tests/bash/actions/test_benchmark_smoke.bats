#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "benchmark-smoke runs pytest" {
  run_action "$REPO_ROOT/.github/actions/benchmark-smoke" pytest-args="-k fast"
  assert_exit_code 0
  grep -q "pytest" "$FAKEBIN_LOG"
}

@test "benchmark-smoke propagates pytest failure" {
  FAKEBIN_FAIL_PYTEST=1
  # override pytest stub locally
  cat > "$REPO_ROOT/tests/fakebin/pytest" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "pytest $@" >> "${FAKEBIN_LOG:?}"
exit 2
EOF
  chmod +x "$REPO_ROOT/tests/fakebin/pytest"

  run_action "$REPO_ROOT/.github/actions/benchmark-smoke" pytest-args="-k fast"
  assert_exit_code 2
}

