# Rust Crate Example

Demonstrates the reusable Rust CI workflow.

```yaml
# .github/workflows/ci.yml
name: ci
on:
  push:
  pull_request:
jobs:
  rust:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-ci.yml@develop
```

Until the first stable release is cut, examples use `@develop`. For production adoption, pin an exact commit SHA.
