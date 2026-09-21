#!/usr/bin/env bash
set -euo pipefail

body="${PR_BODY:-}"
if [ -z "$(echo "$body" | tr -d '[:space:]')" ]; then
  echo "::error::Pull request description is empty";
  exit 1;
fi
for section in "## Summary" "## Testing"; do
  if ! echo "$body" | grep -q "$section"; then
    echo "::error::Missing '$section' section in PR description";
    exit 1;
  fi
done
echo "PR description contains required sections"
