#!/usr/bin/env bash
set -euo pipefail

test_directory="${INPUT_TEST_DIRECTORY:-tests/testthat}"
install_dependencies="${INPUT_INSTALL_DEPENDENCIES:-true}"
use_devtools="${INPUT_USE_DEVTOOLS:-true}"
working_directory="${INPUT_WORKING_DIRECTORY:-.}"

Rscript "$(dirname "$0")/test.R" "$test_directory" "$install_dependencies" "$use_devtools" "$working_directory"
