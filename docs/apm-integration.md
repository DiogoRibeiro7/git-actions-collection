# APM Integration Action

Integrate application performance monitoring into deployments with support for
Datadog, New Relic, and Azure Application Insights.

## Features

- Sends deployment events with environment metadata
- Uploads custom metrics and warns on performance regressions
- Works with Docker and cloud deployment workflows
- Helps establish SLO/SLA monitoring across providers

## Inputs

See [action README](../.github/actions/apm-integration/README.md#inputs) for full
details.

## Usage

```yaml
- uses: DiogoRibeiro7/gh-actions-collection/.github/actions/apm-integration@main
  with:
    provider: newrelic
    api-key: ${{ secrets.NR_API_KEY }}
    app-id: 12345
    environment: production
    metrics-file: metrics.json
```

## Setup Instructions

1. Create an API key for your monitoring provider.
2. Grant permissions to post deployment markers and custom metrics.
3. Add the key as a repository secret (e.g., `DD_API_KEY`).
4. Optionally generate a `metrics.json` file with `latency` and `threshold`
   values prior to invoking the action.

## Troubleshooting

- **401 Unauthorized**: Verify the API key and account region.
- **Missing app-id**: New Relic requires an application ID; supply via
  `app-id` input.
- **No metrics uploaded**: Ensure `metrics-file` path is correct and contains
  valid JSON.

## Performance Tips

- Cache metric collection scripts to keep runtime under two minutes.
- Limit custom metrics to high-value indicators to control costs.

## Security Considerations

- Avoid including personally identifiable information in metrics.
- Rotate API keys regularly and store them in GitHub Secrets.
- Use separate keys per environment to isolate access.

## Migration Guide

To migrate existing deployments:

1. Insert this action after your deploy step.
2. Remove any bespoke curl-based monitoring hooks.
3. Validate that deployment events appear in your monitoring dashboard.
