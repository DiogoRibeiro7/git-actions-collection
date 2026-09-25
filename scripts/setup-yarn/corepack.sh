#!/usr/bin/env bash
set -euo pipefail

# Node.js 25 and newer no longer bundle Corepack.
if [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 25 ]; then
  npm install --global corepack@0.36.0
fi
corepack enable
