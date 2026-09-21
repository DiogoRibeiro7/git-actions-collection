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
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/go-ci.yml@develop
```

Until the first stable release is cut, examples use `@develop`. For production adoption, pin an exact commit SHA.
