# Helm Chart Example

Uses the `helm-chart-lint-test` workflow to lint and dry-run template a chart.

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/helm-chart-lint-test.yml@v1
    with:
      chart-path: .
```

Examples use the stable `@v1` tag. Pin an exact commit SHA when immutable reproducibility is required.
