# APM Integration Example

Demonstrates notifying Datadog after a deployment.

## Workflow

```yaml
- name: APM notify
  uses: DiogoRibeiro7/git-actions-collection/.github/actions/apm-integration@v1
  with:
    provider: datadog
    api-key: ${{ secrets.DD_API_KEY }}
    environment: demo
```

Examples use the stable `@v1` tag. Pin an exact commit SHA when immutable reproducibility is required.

## Setup

1. Create a Datadog API key with events write permissions.
2. Add the key as `DD_API_KEY` repository secret.
3. Trigger the workflow by pushing to `main`.
