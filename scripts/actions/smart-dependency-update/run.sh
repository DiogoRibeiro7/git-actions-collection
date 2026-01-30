#!/usr/bin/env bash
set -euo pipefail

manifests="${INPUT_MANIFESTS:-}"
apply="${INPUT_APPLY:-false}"
batch_size="${INPUT_BATCH_SIZE:-50}"
dependabot="${INPUT_DEPENDABOT:-false}"
repo="${INPUT_REPO:-}"
pip_version="${INPUT_PIP_VERSION:-24.3.1}"
script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"

if [ -z "$manifests" ]; then
  echo "manifests input is required" >&2
  exit 1
fi

if [ "$pip_version" = "latest" ]; then
  python -m pip install --upgrade pip
else
  python -m pip install --upgrade "pip==$pip_version"
fi
pip install tomlkit==0.13.3 packaging==24.2 requests==2.32.3

apply_flag=""
if [ "$apply" = "true" ]; then
  apply_flag="--apply"
fi

alert_flag=""
if [ "$dependabot" = "true" ]; then
  alert_flag="--dependabot"
fi

repo_flag=""
if [ -n "$repo" ]; then
  repo_flag="--repo $repo"
fi

report=$(python "$repo_root/scripts/smart_dependency_update.py" --manifests $manifests $apply_flag --batch-size "$batch_size" $alert_flag $repo_flag)
if [ -z "${GITHUB_OUTPUT:-}" ]; then
  echo "GITHUB_OUTPUT is not set" >&2
  exit 1
fi
echo "report=$report" >> "$GITHUB_OUTPUT"
