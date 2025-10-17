# Helm Chart Example

Uses the `helm-chart-lint-test` workflow to lint and dry-run template a chart.

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/helm-chart-lint-test.yml@main
    with:
      chart-path: .
```
