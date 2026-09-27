#!/usr/bin/env bash
set -euo pipefail

provider="${INPUT_PROVIDER:-}"
api_key="${INPUT_API_KEY:-}"
app_id="${INPUT_APP_ID:-}"
environment="${INPUT_ENVIRONMENT:-production}"
deployment_id="${INPUT_DEPLOYMENT_ID:-}"
metrics_file="${INPUT_METRICS_FILE:-}"
api_url="${INPUT_API_URL:-}"

if [ -z "$provider" ]; then
  echo "::error::provider is required" >&2
  exit 1
fi
if [ -z "$api_key" ]; then
  echo "::error::api-key is required" >&2
  exit 1
fi

case "$provider" in
  datadog|newrelic|appinsights) ;;
  *) echo '::error::Unsupported provider' >&2; exit 1 ;;
 esac

# Quote a value as a JSON string. Inputs used to be pasted into the payload
# unescaped, so a quote or backslash in `environment` produced invalid JSON.
json_string() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\r'/\\r}"
  value="${value//$'\t'/\\t}"
  printf '"%s"' "$value"
}

id_json="$(json_string "$deployment_id")"
env_json="$(json_string "$environment")"

# `api-url` replaces the provider's default endpoint, for other regions or a proxy.
case "$provider" in
  datadog)
    url="${api_url:-https://api.datadoghq.com/api/v1/events}"
    payload="{\"title\":$(json_string "Deployment $deployment_id"),\"text\":$(json_string "Environment: $environment"),\"tags\":[$(json_string "env:$environment")],\"alert_type\":\"info\"}"
    curl -fsS -H "DD-API-KEY:$api_key" -H 'Content-Type: application/json' -d "$payload" "$url"
    ;;
  newrelic)
    if [ -z "$app_id" ] && [ -z "$api_url" ]; then
      echo '::error::app-id is required for New Relic' >&2
      exit 1
    fi
    url="${api_url:-https://api.newrelic.com/v2/applications/$app_id/deployments.json}"
    payload="{\"deployment\":{\"revision\":$id_json,\"user\":\"github-actions\",\"description\":\"Deployment\"}}"
    curl -fsS -H "Api-Key:$api_key" -H 'Content-Type: application/json' -d "$payload" "$url"
    ;;
  appinsights)
    url="${api_url:-https://dc.services.visualstudio.com/v2/track}"
    time_json="$(json_string "$(date -u +%Y-%m-%dT%H:%M:%SZ)")"
    payload="{\"name\":\"Microsoft.ApplicationInsights.Event\",\"time\":$time_json,\"iKey\":$(json_string "$api_key"),\"data\":{\"baseType\":\"EventData\",\"baseData\":{\"name\":\"deployment\",\"properties\":{\"deploymentId\":$id_json,\"environment\":$env_json}}}}"
    curl -fsS -H 'Content-Type: application/json' -d "$payload" "$url"
    ;;
esac

if [ -n "$metrics_file" ]; then
  latency=$(jq -r '.latency // empty' "$metrics_file" || true)
  threshold=$(jq -r '.threshold // empty' "$metrics_file" || true)
  number='^-?[0-9]+([.][0-9]+)?$'
  if [[ "$latency" =~ $number ]] && [[ "$threshold" =~ $number ]]; then
    # awk compares decimals, which bash's -gt rejected.
    if awk -v latency="$latency" -v threshold="$threshold" 'BEGIN { exit !(latency > threshold) }'; then
      echo "::warning::latency $latency exceeded threshold $threshold"
    fi
  elif [ -n "$latency$threshold" ]; then
    echo "::warning::metrics-file needs numeric latency and threshold values"
  fi
fi
