#!/usr/bin/env bash
set -euo pipefail

pip_version="${INPUT_PIP_VERSION:-24.3.1}"

if [ "$pip_version" = "latest" ]; then
  python -m pip install --upgrade pip
else
  python -m pip install --upgrade "pip==$pip_version"
fi
pip install pytest==8.4.1 pytest-benchmark==5.1.0
