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
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/go-ci.yml@main
```
