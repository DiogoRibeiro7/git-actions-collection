#!/usr/bin/env bash
set -euo pipefail

pip_version="${INPUT_PIP_VERSION:-26.2.1}"

if [ "$pip_version" = "latest" ]; then
  python -m pip install --upgrade pip
else
  python -m pip install --upgrade "pip==$pip_version"
fi

pip install poetry==2.5.1
