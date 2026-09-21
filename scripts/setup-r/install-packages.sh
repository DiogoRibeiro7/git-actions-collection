#!/usr/bin/env bash
set -euo pipefail

packages="${INPUT_PACKAGES:-}"
cran_mirror="${INPUT_CRAN_MIRROR:-https://cloud.r-project.org}"
working_directory="${INPUT_WORKING_DIRECTORY:-.}"

if [ -z "$packages" ]; then
  exit 0
fi

Rscript "$(dirname "$0")/install-packages.R" "$packages" "$cran_mirror" "$working_directory"
