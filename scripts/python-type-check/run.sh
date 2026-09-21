#!/usr/bin/env bash
set -euo pipefail

requirements_file="${INPUT_REQUIREMENTS_FILE:-}"
extra_deps="${INPUT_EXTRA_DEPENDENCIES:-}"
mypy_args="${INPUT_MYPY_ARGS:-.}"
pip_version="${INPUT_PIP_VERSION:-24.3.1}"

if [ "$pip_version" = "latest" ]; then
  python -m pip install --upgrade pip
else
  python -m pip install --upgrade "pip==$pip_version"
fi

if [ -n "$requirements_file" ]; then
  python -m pip install -r "$requirements_file"
fi

if [ -n "$extra_deps" ]; then
  python -m pip install $extra_deps
fi

python -m pip install mypy
mypy $mypy_args
