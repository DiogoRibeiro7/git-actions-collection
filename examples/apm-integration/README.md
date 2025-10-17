# APM Integration Example

Demonstrates notifying Datadog after a deployment.

## Workflow

```yaml
- name: APM notify
  uses: DiogoRibeiro7/gh-actions-collection/.github/actions/apm-integration@main
  with:
    provider: datadog
    api-key: ${{ secrets.DD_API_KEY }}
    environment: demo
```

## Setup

1. Create a Datadog API key with events write permissions.
2. Add the key as `DD_API_KEY` repository secret.
3. Trigger the workflow by pushing to `main`.
