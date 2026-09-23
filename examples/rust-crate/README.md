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
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-ci.yml@v1
```

Examples use the stable `@v1` tag. Pin an exact commit SHA when immutable reproducibility is required.
