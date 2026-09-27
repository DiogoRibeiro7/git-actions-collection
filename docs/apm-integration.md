# APM Integration Action

Record deployments in application performance monitoring with support for
Datadog, New Relic, and Azure Application Insights.

## Features

- Sends a deployment event tagged with the environment
- Warns in the job log when a measured latency exceeds its threshold
- Reaches other regions or a proxy through `api-url`
- Works after any deployment step, such as Docker or cloud deployments

The action does not upload metrics to the provider. `metrics-file` only feeds
the latency warning.

## Inputs

See [action README](../.github/actions/apm-integration/README.md#inputs) for full
details.

## Usage

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/apm-integration@v1
  with:
    provider: newrelic
    api-key: ${{ secrets.NR_API_KEY }}
    app-id: 12345
    environment: production
    metrics-file: metrics.json
```

For Datadog sites other than US1, New Relic's EU region, or an Application
Insights ingestion endpoint from a connection string, set `api-url`; the
[action README](../.github/actions/apm-integration/README.md#other-regions-and-proxies)
lists the URLs.

## Setup Instructions

1. Create a key that can post events (Datadog) or deployment markers (New
   Relic), or copy the Application Insights instrumentation key.
2. Add the key as a repository secret (e.g., `DD_API_KEY`).
3. Optionally write a `metrics.json` file with numeric `latency` and `threshold`
   values before invoking the action.

## Troubleshooting

- **401 or 403**: Verify the API key, and set `api-url` if the account is in
  another region.
- **Missing app-id**: New Relic needs an application ID, through `app-id` or an
  `api-url` that contains it.
- **No latency warning**: Check that `metrics-file` points to JSON with numeric
  `latency` and `threshold` values; other values produce their own warning.

## Security Considerations

- Rotate API keys regularly and store them in GitHub Secrets.
- Use separate keys per environment to isolate access.

## Migration Guide

To migrate existing deployments:

1. Insert this action after your deploy step.
2. Remove any bespoke curl-based monitoring hooks.
3. Validate that deployment events appear in your monitoring dashboard.
