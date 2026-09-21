#!/usr/bin/env bash
set -euo pipefail

pytest_args="${INPUT_PYTEST_ARGS:-}"

pytest $pytest_args --benchmark-only --benchmark-json=benchmark.json
