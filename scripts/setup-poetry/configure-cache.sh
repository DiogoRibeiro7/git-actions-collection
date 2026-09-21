#!/usr/bin/env bash
set -euo pipefail

if [ -z "${GITHUB_ENV:-}" ]; then
  echo "GITHUB_ENV is not set" >&2
  exit 1
fi

echo "POETRY_CACHE_DIR=$HOME/.cache/pypoetry" >> "$GITHUB_ENV"
