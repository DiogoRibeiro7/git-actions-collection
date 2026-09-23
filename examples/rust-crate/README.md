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

The primary job also uses a best-effort Cargo cache by default. Cache restoration or
saving is an optimisation only: cache failures are allowed to continue and therefore
cannot turn a valid build into a CI failure. Set `use-cache: false` when a repository
needs a fully cold CI run, or `cache-targets: false` to cache only Cargo registry data.

For repositories that want a separate fast quality gate, use the dedicated
`rust-quality.yml` workflow. It runs `rustfmt` and Clippy without running the
full test suite:

```yaml
jobs:
  quality:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-quality.yml@v1
    with:
      all-features: true
```

Rust dependency vulnerabilities can be checked independently with the security workflow:

```yaml
jobs:
  security:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-security.yml@v1
```

The workflow runs RustSec `cargo-audit` with read-only repository permissions. Library
crates that do not commit `Cargo.lock` can use the default temporary lockfile generation.
Known non-applicable RustSec advisories may be passed explicitly through
`ignored-advisories`.

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
