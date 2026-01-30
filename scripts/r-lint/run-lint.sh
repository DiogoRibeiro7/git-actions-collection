#!/usr/bin/env bash
set -euo pipefail

working_dir="${INPUT_WORKING_DIRECTORY:-.}"
config_file="${INPUT_CONFIG_FILE:-}"
targets="${INPUT_TARGETS:-R}"

Rscript "$(dirname "$0")/lint.R" "$config_file" "$targets" "$working_dir"
