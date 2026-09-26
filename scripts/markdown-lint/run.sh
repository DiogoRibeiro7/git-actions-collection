#!/usr/bin/env bash
set -euo pipefail

paths="${INPUT_PATHS:-.}"
config_file="${INPUT_CONFIG_FILE:-}"

npm install -g markdownlint-cli@0.42.0

# `paths` lists files, directories or globs separated by spaces or newlines. Passed
# as one argument, "docs README.md" named a single path that does not exist. Each
# entry stays quoted, so markdownlint expands globs itself.
read -r -d '' -a targets <<< "$paths" || true
# Installed dependencies ship their own Markdown, which is not the caller's to fix.
args=(--ignore '**/node_modules/**')
if [ -n "$config_file" ]; then
  args+=(-c "$config_file")
fi

output="$(mktemp)"
status=0
markdownlint "${args[@]}" "${targets[@]}" > "$output" 2>&1 || status=$?
cat "$output"
# When no file matches, markdownlint prints its usage and exits 0, which would pass
# the check without linting anything.
if [ "$status" -eq 0 ] && grep -q '^Usage: markdownlint' "$output"; then
  echo "::error::No Markdown files matched paths: $paths" >&2
  exit 1
fi
exit "$status"
