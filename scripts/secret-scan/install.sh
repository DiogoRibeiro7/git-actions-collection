#!/usr/bin/env bash
set -euo pipefail

# Installs a fixed, checksummed gitleaks release. gitleaks-action, used before,
# accepted no inputs, needed GITHUB_TOKEN to scan pull requests, and needed a
# licence key for repositories owned by an organisation.
version="8.30.1"
case "$(uname -s)-$(uname -m)" in
  Linux-x86_64)
    platform="linux_x64"
    sha256="551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"
    ;;
  Linux-aarch64 | Linux-arm64)
    platform="linux_arm64"
    sha256="e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080"
    ;;
  *)
    echo "::error::secret-scan runs on Linux x64 and arm64 runners, not $(uname -s) $(uname -m)" >&2
    exit 1
    ;;
esac

if [ -z "${RUNNER_TEMP:-}" ] || [ -z "${GITHUB_PATH:-}" ]; then
  echo "RUNNER_TEMP and GITHUB_PATH must be set" >&2
  exit 1
fi

archive="$RUNNER_TEMP/gitleaks.tar.gz"
curl -fsSL -o "$archive" \
  "https://github.com/gitleaks/gitleaks/releases/download/v$version/gitleaks_${version}_${platform}.tar.gz"
echo "$sha256  $archive" | sha256sum --check --quiet
mkdir -p "$RUNNER_TEMP/gitleaks"
tar -xzf "$archive" -C "$RUNNER_TEMP/gitleaks" gitleaks
echo "$RUNNER_TEMP/gitleaks" >> "$GITHUB_PATH"
