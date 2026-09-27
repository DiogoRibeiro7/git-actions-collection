# APM Integration

Send a deployment event to Datadog, New Relic, or Azure Application Insights,
and warn when a measured latency exceeds its threshold.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `provider` | yes |  | APM provider: datadog, newrelic, or appinsights |
| `api-key` | yes |  | API or ingestion key for the provider |
| `app-id` | no |  | Application or service identifier (required for New Relic unless api-url is set) |
| `environment` | no | `production` | Deployment environment name |
| `deployment-id` | no | `${{ github.sha }}` | Identifier for the deployment event |
| `metrics-file` | no |  | Optional JSON file with numeric latency and threshold values; the action warns when latency exceeds threshold |
| `api-url` | no |  | Full URL to send the event to instead of the provider's default, for another region or a proxy; for New Relic it replaces the need for app-id |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Usage

```yaml
- name: Record the deployment
  uses: DiogoRibeiro7/git-actions-collection/.github/actions/apm-integration@v1
  with:
    provider: datadog
    api-key: ${{ secrets.DD_API_KEY }}
    environment: staging
```

## What it sends

| Provider | Default endpoint | Request |
| --- | --- | --- |
| `datadog` | `https://api.datadoghq.com/api/v1/events` | An event titled `Deployment <deployment-id>`, tagged `env:<environment>`, with the key in `DD-API-KEY`. |
| `newrelic` | `https://api.newrelic.com/v2/applications/<app-id>/deployments.json` | A deployment marker with revision `<deployment-id>`, with the key in `Api-Key`. |
| `appinsights` | `https://dc.services.visualstudio.com/v2/track` | A custom event named `deployment` whose `iKey` is `api-key`, with the deployment ID and environment as properties. |

The action escapes `environment`, `deployment-id`, and `api-key` as JSON strings,
so quotes or backslashes in them cannot break the request. A request the provider
rejects fails the step. It needs `curl`, and `jq` only when `metrics-file` is set.

## Other regions and proxies

The default endpoints are Datadog's US1 site, New Relic's US region, and Azure's
global ingestion endpoint. Set `api-url` to the full URL for another region or
for a proxy:

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/apm-integration@v1
  with:
    provider: datadog
    api-key: ${{ secrets.DD_API_KEY }}
    api-url: https://api.datadoghq.eu/api/v1/events
```

- Datadog: `https://api.<site>/api/v1/events`, for example `datadoghq.eu`,
  `us3.datadoghq.com`, `us5.datadoghq.com`, or `ap1.datadoghq.com`.
- New Relic EU: `https://api.eu.newrelic.com/v2/applications/<app-id>/deployments.json`.
  With `api-url` set, `app-id` is not needed because the URL already names the
  application.
- Application Insights: Microsoft ended support for ingestion by
  instrumentation key alone on 31 March 2025 in favour of connection strings.
  Use the `IngestionEndpoint` from your connection string followed by
  `v2/track`, for example
  `https://westeurope-5.in.applicationinsights.azure.com/v2/track`, and keep the
  instrumentation key in `api-key`.

## Latency warnings

`metrics-file` names a JSON file such as `{"latency": 120.5, "threshold": 100}`.
When both values are numbers and `latency` is greater, the action logs a
warning; it does not fail the step and does not send the values to the
provider. A file whose values are not numbers also produces a warning.

## Troubleshooting

- A `401` or `403` means the key is wrong or was issued for another region; set
  `api-url` for that region.
- For New Relic, supply the `app-id` associated with the application, or an
  `api-url` that contains it.

## Security Considerations

- Pass API keys via GitHub Secrets and never hard-code them in workflows.
- Run the action after the deployment succeeds, so failed deployments do not
  appear as markers.
