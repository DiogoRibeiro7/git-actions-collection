#!/usr/bin/env bash
set -euo pipefail

load "$(dirname "$BATS_TEST_FILENAME")/../lib/action_harness.bash"

@test "apm-integration fails without provider" {
  run_action "$REPO_ROOT/.github/actions/apm-integration" api-key=token
  assert_exit_code 1
}

@test "apm-integration calls curl" {
  run_action "$REPO_ROOT/.github/actions/apm-integration" provider=datadog api-key=token deployment-id=abc
  assert_exit_code 0
  grep -q "curl" "$FAKEBIN_LOG"
}

@test "apm-integration sends to api-url instead of the default endpoint" {
  run_action "$REPO_ROOT/.github/actions/apm-integration" provider=datadog api-key=token \
    deployment-id=abc api-url=https://api.datadoghq.eu/api/v1/events
  assert_exit_code 0
  grep -q "https://api.datadoghq.eu/api/v1/events" "$FAKEBIN_LOG"
  run grep -q "api.datadoghq.com" "$FAKEBIN_LOG"
  [ "$status" -ne 0 ]
}

@test "apm-integration accepts a New Relic api-url without app-id" {
  run_action "$REPO_ROOT/.github/actions/apm-integration" provider=newrelic api-key=token \
    deployment-id=abc api-url=https://api.eu.newrelic.com/v2/applications/42/deployments.json
  assert_exit_code 0
  grep -q "https://api.eu.newrelic.com/v2/applications/42/deployments.json" "$FAKEBIN_LOG"
}

@test "apm-integration still needs app-id for New Relic without api-url" {
  run_action "$REPO_ROOT/.github/actions/apm-integration" provider=newrelic api-key=token deployment-id=abc
  assert_exit_code 1
}

