#!/usr/bin/env bash
set -euo pipefail

paths="${INPUT_PATHS:-.}"
config_file="${INPUT_CONFIG_FILE:-}"

npm install -g markdownlint-cli@0.42.0
if [ -n "$config_file" ]; then
  markdownlint -c "$config_file" "$paths"
else
  markdownlint "$paths"
fi
