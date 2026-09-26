# Go Module Example

Uses the reusable Go CI workflow to run tests and lint with `golangci-lint`.

```yaml
# .github/workflows/ci.yml
name: ci
on:
  push:
  pull_request:
jobs:
  go:
    permissions:
      contents: read
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/go-ci.yml@v1
```

Examples use the stable `@v1` tag. Pin an exact commit SHA when immutable reproducibility is required.
