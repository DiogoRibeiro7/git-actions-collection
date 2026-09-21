setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
  TEST_TMPDIR=$(mktemp -d)
  FAKEBIN="$TEST_TMPDIR/fakebin"
  mkdir -p "$FAKEBIN"
  export PATH="$FAKEBIN:$PATH"
  export GITHUB_OUTPUT="$TEST_TMPDIR/github_output"
  export GITHUB_ENV="$TEST_TMPDIR/github_env"
  : > "$GITHUB_OUTPUT"
  : > "$GITHUB_ENV"
  export COMMAND_LOG="$TEST_TMPDIR/commands.log"
  : > "$COMMAND_LOG"
  cd "$TEST_TMPDIR"
}

teardown() {
  cd "$REPO_ROOT"
  rm -rf "$TEST_TMPDIR"
}

make_fake() {
  local name="$1"
  shift
  {
    echo '#!/usr/bin/env bash'
    printf '%s\n' "$@"
  } > "$FAKEBIN/$name"
  chmod +x "$FAKEBIN/$name"
}

make_logger() {
  local name="$1"
  cat > "$FAKEBIN/$name" <<EOF
#!/usr/bin/env bash
echo "$name \$@" >> "$COMMAND_LOG"
EOF
  chmod +x "$FAKEBIN/$name"
}
