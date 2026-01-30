#!/usr/bin/env bash
set -euo pipefail

extras="${INPUT_ADDITIONAL_PACKAGES:-}"
if [ -n "$extras" ]; then
  packages="lintr,$extras"
else
  packages="lintr"
fi

if [ -z "${GITHUB_OUTPUT:-}" ]; then
  echo "GITHUB_OUTPUT is not set" >&2
  exit 1
fi

echo "packages=$packages" >> "$GITHUB_OUTPUT"
