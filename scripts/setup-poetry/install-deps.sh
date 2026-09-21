#!/usr/bin/env bash
set -euo pipefail

poetry --version
poetry install --no-interaction --no-root
