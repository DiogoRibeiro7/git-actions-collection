#!/usr/bin/env bash
set -euo pipefail

paths="${INPUT_PATHS:-src tests}"
smart_update="${INPUT_SMART_UPDATE:-false}"
script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"

python "$repo_root/scripts/check_imports_vs_pyproject.py" --paths $paths --fail-on none --format text --update
if [ "$smart_update" = "true" ]; then
  python "$repo_root/scripts/smart_dependency_update.py" --manifests pyproject.toml --apply
fi
