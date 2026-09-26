#!/usr/bin/env bash
set -euo pipefail

# Defaults belong to action.yml. Using `${VAR-}` here preserves an explicitly
# empty input so validation can reject it instead of silently replacing it.
src="${INPUT_SRC-}"
output_zip="${INPUT_OUTPUT_ZIP-}"
pip_version="${INPUT_PIP_VERSION:-26.2.1}"

if [ -z "$src" ]; then
  echo "src input must not be empty" >&2
  exit 1
fi
if [ -z "$output_zip" ]; then
  echo "output-zip input must not be empty" >&2
  exit 1
fi

if [ "$pip_version" = "latest" ]; then
  python -m pip install --upgrade pip
else
  python -m pip install --upgrade "pip==$pip_version"
fi

# zip runs inside build/, so resolve the archive path first and create its
# directory: a relative path outside artifact/ used to fail, and an absolute
# one was written under the workspace instead.
case "$output_zip" in
  /*) output_path="$output_zip" ;;
  *) output_path="$PWD/$output_zip" ;;
esac
mkdir -p "$(dirname "$output_path")" build/python
# zip -r adds to an existing archive, which would keep files from an older build.
rm -f "$output_path"

rsync -av --exclude '__pycache__' --exclude '*.pyc' "$src/" build/
if [ -f "$src/requirements.txt" ]; then
  pip install -r "$src/requirements.txt" -t build/
fi

(cd build && zip -r "$output_path" .)
echo "Created $output_zip"
