# APM Integration

Send deployment notifications and custom metrics to popular APM providers.

## Inputs

| Name | Description | Default |
|------|-------------|---------|
| `provider` | APM provider: `datadog`, `newrelic`, or `appinsights` | – |
| `api-key` | API or ingestion key for the provider | – |
| `app-id` | Application identifier (required for New Relic) | – |
| `environment` | Deployment environment name | `production` |
| `deployment-id` | Identifier for the deployment event | commit SHA |
| `metrics-file` | Path to JSON metrics file with `latency` and `threshold` | – |

## Outputs

None

## Usage

```yaml
actions-apm:
  uses: DiogoRibeiro7/gh-actions-collection/.github/actions/apm-integration@main
  with:
    provider: datadog
    api-key: ${{ secrets.DD_API_KEY }}
    environment: staging
```

## Troubleshooting

- Ensure the API key has permissions to publish deployment events.
- For New Relic, supply the `app-id` associated with the application.
- Provide a `metrics-file` containing numeric `latency` and `threshold` values
  to enable regression warnings.

## Performance Tips

- Only send metrics that are necessary to avoid exceeding provider quotas.
- Run the action after successful deployments to minimize noise.

## Security Considerations

- Pass API keys via GitHub Secrets and never hard‑code them in workflows.
- Metrics may contain sensitive data; sanitize before uploading.
