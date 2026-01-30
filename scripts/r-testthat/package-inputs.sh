#!/usr/bin/env bash
set -euo pipefail

use_devtools="${INPUT_USE_DEVTOOLS:-true}"
extras="${INPUT_ADDITIONAL_PACKAGES:-}"

pkgs="remotes,testthat"
if [ "$use_devtools" = "true" ]; then
  pkgs="$pkgs,devtools"
fi
if [ -n "$extras" ]; then
  pkgs="$pkgs,$extras"
fi

if [ -z "${GITHUB_OUTPUT:-}" ]; then
  echo "GITHUB_OUTPUT is not set" >&2
  exit 1
fi

echo "packages=$pkgs" >> "$GITHUB_OUTPUT"
