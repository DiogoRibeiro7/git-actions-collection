#!/usr/bin/env bash
set -euo pipefail

working_directory="${INPUT_WORKING_DIRECTORY:-.}"

cd "$working_directory"
if [ -f yarn.lock ]; then
  # Yarn 1 accepts --immutable but ignores it, so a lockfile out of step with
  # package.json was silently rewritten. Its equivalent is --frozen-lockfile.
  if [ "$(yarn --version | cut -d. -f1)" = "1" ]; then
    yarn install --frozen-lockfile
  else
    yarn install --immutable
  fi
else
  echo "No yarn.lock found"
fi
