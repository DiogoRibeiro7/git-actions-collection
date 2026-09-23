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

The default invocation runs the primary Ubuntu/stable quality and test job only.

Projects that need explicit Cargo features can pass `features`, `all-features`, or
`no-default-features`. Compatibility testing is opt-in so ordinary pull requests
do not automatically multiply Actions usage:

```yaml
jobs:
  rust:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-ci.yml@v1
    with:
      all-features: true
      run-compatibility: true
      compatibility-toolchains: '["stable", "beta", "nightly", "1.85.0"]'
      compatibility-os: '["ubuntu-latest", "windows-latest", "macos-latest"]'
```

A pinned version such as `1.85.0` can represent the project's minimum supported
Rust version (MSRV).

Examples use the stable `@v1` tag. Pin an exact commit SHA when immutable reproducibility is required.
