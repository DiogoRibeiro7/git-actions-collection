#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "gradle-build fails without tasks" {
  RUN_ACTION_WORKSPACE="$(mktemp -d)" run_action "$REPO_ROOT/.github/actions/gradle-build" tasks= working-directory="$RUN_ACTION_WORKSPACE"
  assert_exit_code 1
}

@test "gradle-build calls gradlew" {
  local_ws="$(mktemp -d)"
  echo '#!/usr/bin/env bash
./gradlew "$@"' > "$local_ws/gradlew"
  chmod +x "$local_ws/gradlew"
  RUN_ACTION_WORKSPACE="$local_ws" run_action "$REPO_ROOT/.github/actions/gradle-build" tasks=build gradle-args=--info working-directory="$local_ws"
  assert_exit_code 0
  grep -q "gradlew" "$FAKEBIN_LOG"
}

