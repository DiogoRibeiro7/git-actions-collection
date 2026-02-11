#!/usr/bin/env bash
set -euo pipefail

src="${INPUT_SRC:-lambda/}"
output_zip="${INPUT_OUTPUT_ZIP:-artifact/lambda.zip}"
pip_version="${INPUT_PIP_VERSION:-24.3.1}"

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

mkdir -p artifact build/python
rsync -av --exclude '__pycache__' --exclude '*.pyc' "$src/" build/
if [ -f "$src/requirements.txt" ]; then
  pip install -r "$src/requirements.txt" -t build/
fi

(cd build && zip -r "../$output_zip" .)
echo "Created $output_zip"
