#!/usr/bin/env bash
set -euo pipefail

# Defaults belong to action.yml; `${VAR-}` keeps an explicitly empty input empty.
args="${INPUT_ARGS---no-git -v}"
read -r -d '' -a arg_arr <<< "$args" || true

# --redact comes first so a caller's own --redact=<percent> still wins. Without it,
# a finding printed by -v would show the secret in the job log.
gitleaks detect --redact "${arg_arr[@]}"
