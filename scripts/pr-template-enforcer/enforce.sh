#!/usr/bin/env bash
set -euo pipefail

body="${PR_BODY:-}"
# Defaults belong to action.yml; this fallback keeps direct calls working.
default_sections=$'## Summary\n## Testing'
sections="${INPUT_REQUIRED_SECTIONS-$default_sections}"

if [ -z "$(printf '%s' "$body" | tr -d '[:space:]')" ]; then
  echo "::error::Pull request description is empty"
  exit 1
fi

missing=0
while IFS= read -r section; do
  # Trim surrounding whitespace so an indented YAML block still matches.
  section="${section#"${section%%[![:space:]]*}"}"
  section="${section%"${section##*[![:space:]]}"}"
  if [ -z "$section" ]; then
    continue
  fi
  # A fixed-string match: headings like `## C++ notes` must not act as a regex.
  if ! grep -qF -- "$section" <<< "$body"; then
    echo "::error::Missing '$section' section in PR description"
    missing=1
  fi
done <<< "$sections"

if [ "$missing" -ne 0 ]; then
  exit 1
fi
echo "PR description contains required sections"
