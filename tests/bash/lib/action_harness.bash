#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

run_action() {
  local action_dir="$1"
  shift || true

  local action_file="$action_dir/action.yml"
  if [ ! -f "$action_file" ]; then
    echo "action.yml not found in $action_dir" >&2
    return 2
  fi

  local temp_dir
  if [ -n "${RUN_ACTION_WORKSPACE:-}" ]; then
    export GITHUB_WORKSPACE="$RUN_ACTION_WORKSPACE"
    mkdir -p "$GITHUB_WORKSPACE"
    temp_dir="$(mktemp -d)"
  else
    temp_dir="$(mktemp -d)"
    export GITHUB_WORKSPACE="$temp_dir/workspace"
    mkdir -p "$GITHUB_WORKSPACE"
  fi

  if [ "${RUN_ACTION_UNSET_GITHUB_OUTPUT:-false}" = "true" ]; then
    unset GITHUB_OUTPUT
  else
    export GITHUB_OUTPUT="$temp_dir/github_output"
    : > "$GITHUB_OUTPUT"
  fi

  export FAKEBIN_LOG="$temp_dir/fakebin.log"
  : > "$FAKEBIN_LOG"

  # Git does not need to preserve executable bits for these tiny test shims.
  # Make them executable explicitly before putting them on PATH so the tests
  # cannot silently fall through to real host commands.
  chmod +x "$REPO_ROOT"/tests/fakebin/*
  export PATH="$REPO_ROOT/tests/fakebin:$PATH"

  local kv
  for kv in "$@"; do
    if [[ "$kv" != *=* ]]; then
      echo "invalid input '$kv' (expected key=value)" >&2
      return 2
    fi
    local key="${kv%%=*}"
    local value="${kv#*=}"
    local env_key
    env_key="INPUT_$(echo "$key" | tr '[:lower:]-' '[:upper:]_')"
    export "$env_key"="$value"
  done

  local stdout_file="$temp_dir/stdout"
  local stderr_file="$temp_dir/stderr"
  : > "$stdout_file"
  : > "$stderr_file"

  local steps
  steps=$(awk '/^[[:space:]]*run: /{sub(/^[[:space:]]*run: /,""); print}' "$action_file")

  local run_cmd
  local status=0
  while IFS= read -r run_cmd; do
    if [ -z "$run_cmd" ]; then
      continue
    fi
    run_cmd=${run_cmd//\"/\\\"}
    run_cmd=${run_cmd//scripts\//"$REPO_ROOT/scripts/"}

    bash -c "cd \"$GITHUB_WORKSPACE\" && $run_cmd" 1>>"$stdout_file" 2>>"$stderr_file" || status=$?
    if [ "$status" -ne 0 ]; then
      break
    fi
  done <<< "$steps"

  export RUN_ACTION_STDOUT="$(cat "$stdout_file" 2>/dev/null || true)"
  export RUN_ACTION_STDERR="$(cat "$stderr_file" 2>/dev/null || true)"
  export RUN_ACTION_EXIT_CODE="$status"

  return 0
}

assert_exit_code() {
  local expected="$1"
  if [ "${RUN_ACTION_EXIT_CODE:-}" != "$expected" ]; then
    echo "expected exit code $expected, got ${RUN_ACTION_EXIT_CODE:-}" >&2
    return 1
  fi
}

assert_output_pair() {
  local key="$1"
  local expected="$2"
  local line
  if [ -z "${GITHUB_OUTPUT:-}" ]; then
    echo "GITHUB_OUTPUT is not available" >&2
    return 1
  fi
  line=$(grep -E "^${key}=" "$GITHUB_OUTPUT" | head -n1 | cut -d= -f2- || true)
  if [ "$line" != "$expected" ]; then
    echo "expected output $key=$expected, got $key=$line" >&2
    return 1
  fi
}

assert_file_exists() {
  local path="$1"
  if [ ! -e "$path" ]; then
    echo "expected file to exist: $path" >&2
    return 1
  fi
}
