# Helm Chart Example

Uses the `helm-chart-lint-test` workflow to lint and dry-run template a chart.

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/helm-chart-lint-test.yml@develop
    with:
      chart-path: .
```

Until the first stable release is cut, examples use `@develop`. For production adoption, pin an exact commit SHA.
