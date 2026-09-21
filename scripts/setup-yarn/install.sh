#!/usr/bin/env bash
set -euo pipefail

working_directory="${INPUT_WORKING_DIRECTORY:-.}"

cd "$working_directory"
if [ -f yarn.lock ]; then
  yarn install --immutable
else
  echo "No yarn.lock found"
fi
