#!/usr/bin/env bash
set -euo pipefail

provider="${INPUT_PROVIDER:-}"
api_key="${INPUT_API_KEY:-}"
app_id="${INPUT_APP_ID:-}"
environment="${INPUT_ENVIRONMENT:-production}"
deployment_id="${INPUT_DEPLOYMENT_ID:-}"
metrics_file="${INPUT_METRICS_FILE:-}"

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

case "$provider" in
  datadog)
    curl -fsS -H "DD-API-KEY:$api_key" -H 'Content-Type: application/json' \
      -d "{\"title\":\"Deployment $deployment_id\",\"text\":\"Environment: $environment\",\"tags\":[\"env:$environment\"],\"alert_type\":\"info\"}" \
      https://api.datadoghq.com/api/v1/events
    ;;
  newrelic)
    if [ -z "$app_id" ]; then
      echo '::error::app-id is required for New Relic' >&2
      exit 1
    fi
    curl -fsS -H "Api-Key:$api_key" -H 'Content-Type: application/json' \
      -d "{\"deployment\":{\"revision\":\"$deployment_id\",\"user\":\"github-actions\",\"description\":\"Deployment\"}}" \
      "https://api.newrelic.com/v2/applications/$app_id/deployments.json"
    ;;
  appinsights)
    curl -fsS -H 'Content-Type: application/json' \
      -d "{\"name\":\"Microsoft.ApplicationInsights.Event\",\"time\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"iKey\":\"$api_key\",\"data\":{\"baseType\":\"EventData\",\"baseData\":{\"name\":\"deployment\",\"properties\":{\"deploymentId\":\"$deployment_id\",\"environment\":\"$environment\"}}}}" \
      https://dc.services.visualstudio.com/v2/track
    ;;
esac

if [ -n "$metrics_file" ]; then
  latency=$(jq -r '.latency // empty' "$metrics_file" || true)
  threshold=$(jq -r '.threshold // empty' "$metrics_file" || true)
  if [ -n "$latency" ] && [ -n "$threshold" ] && [ "$latency" -gt "$threshold" ]; then
    echo "::warning::latency $latency exceeded threshold $threshold"
  fi
fi
