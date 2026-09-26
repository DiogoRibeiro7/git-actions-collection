# Helm Chart Example

`lint.yml` uses the `helm-chart-lint-test` workflow to lint and render the chart on every push:

```yaml
jobs:
  lint:
    permissions:
      contents: read
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/helm-chart-lint-test.yml@v1
    with:
      chart-path: .
```

`release.yml` uses the `helm-chart-release` workflow to package the chart and push it to
`ghcr.io/<owner>/charts` when a `v*` tag is pushed:

```yaml
jobs:
  release:
    permissions:
      contents: read
      packages: write
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/helm-chart-release.yml@v1
    with:
      chart-path: .
      dry-run: false
```

The push runs in the `release` GitHub environment, so protect it with required reviewers if
releases need approval. Without `dry-run: false`, the workflow only lints and packages the chart.
Set `oci-repository` and the `REGISTRY_USERNAME`/`REGISTRY_PASSWORD` secrets to push to another
registry.

Examples use the stable `@v1` tag. Pin an exact commit SHA when immutable reproducibility is required.
