#!/usr/bin/env bash
set -euo pipefail

paths="${INPUT_PATHS:-src tests}"
fail_on="${INPUT_FAIL_ON:-missing}"
format="${INPUT_FORMAT:-text}"
update_pyproject="${INPUT_UPDATE_PYPROJECT:-false}"
pip_version="${INPUT_PIP_VERSION:-24.3.1}"
script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"

if [ -z "${GITHUB_OUTPUT:-}" ]; then
  echo "GITHUB_OUTPUT is not set" >&2
  exit 1
fi

if [ "$pip_version" = "latest" ]; then
  python -m pip install --upgrade pip
else
  python -m pip install --upgrade "pip==$pip_version"
fi
pip install tomlkit==0.13.3

python "$repo_root/scripts/check_imports_vs_pyproject.py" --paths $paths --fail-on none --format json > result.json
missing=$(python -c "import json; print(' '.join(json.load(open(\"result.json\"))['missing']))")
echo "missing=$missing" >> "$GITHUB_OUTPUT"

if [ "$update_pyproject" != "true" ]; then
  python "$repo_root/scripts/check_imports_vs_pyproject.py" --paths $paths --fail-on "$fail_on" --format "$format"
fi
