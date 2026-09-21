#!/usr/bin/env bash
set -euo pipefail

pip_version="${INPUT_PIP_VERSION:-24.3.1}"
enable_mypy="${INPUT_ENABLE_MYPY:-false}"

if [ "$pip_version" = "latest" ]; then
  python -m pip install --upgrade pip
else
  python -m pip install --upgrade "pip==$pip_version"
fi

pip install ruff==0.12.10
if [ "$enable_mypy" = "true" ]; then
  pip install mypy==1.17.1
fi

ruff check .
if [ "$enable_mypy" = "true" ]; then
  mypy .
fi
