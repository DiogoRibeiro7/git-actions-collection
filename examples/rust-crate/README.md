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

`rust-ci.yml`, `rust-quality.yml` and `rust-docs.yml` report problems where you review
code. Compiler, Clippy and rustdoc diagnostics, rustfmt diffs and failing tests become
annotations on the file and line, which a pull request shows in "Files changed". The run
page gets a summary table with each check's result, the error and warning counts, the test
counts and the names of failed tests. The log keeps cargo's usual output, and a check
passes or fails exactly as cargo decides.

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

Projects with an explicit dependency policy can additionally enable `cargo-deny`:

```yaml
jobs:
  security:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-security.yml@v1
    with:
      run-cargo-deny: true
      cargo-deny-config: deny.toml
      cargo-deny-checks: advisories,bans,licenses,sources
```

The `deny.toml` remains owned by the consuming project because licence allowlists,
banned crates, duplicate-version rules, and accepted sources are project policy rather
than sensible global defaults.

Coverage can be run independently with `cargo-llvm-cov`:

```yaml
jobs:
  coverage:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-coverage.yml@v1
    with:
      all-features: true
      minimum-line-coverage: 80
```

The workflow emits a terminal summary and uploads `lcov.info`. The minimum is
caller-defined; a value of `0` disables threshold enforcement.

Rust documentation can be enforced independently:

```yaml
jobs:
  docs:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-docs.yml@v1
    with:
      all-features: true
```

The workflow sets `RUSTDOCFLAGS=-D warnings`, so broken intra-doc links and other
rustdoc warnings fail CI. Dependency documentation is skipped by default, and generated
HTML can be uploaded explicitly with `upload-docs: true`.

Criterion benchmarks can be smoke-tested independently:

```yaml
jobs:
  benchmark:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-benchmark.yml@v1
    with:
      bench-name: add
```

The defaults intentionally use short warm-up and measurement windows. This checks that
benchmark targets compile and execute in CI; it is not a performance-regression threshold.
Hosted runner timing is too noisy for that to be a reliable default. Criterion output can
be retained explicitly with `upload-results: true`.

Before publication, crate metadata and the packaged archive can be verified independently:

```yaml
jobs:
  release-preflight:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-release-preflight.yml@v1
    with:
      package-name: rust-crate
```

The preflight requires release metadata such as licence, description, repository, and
README by default, then runs a verified `cargo package`. In workspaces with multiple
publishable crates, `package-name` must be explicit so the workflow never selects a
release target implicitly; see [`../rust-workspace`](../rust-workspace) for releasing
several workspace crates together. Uploading the generated `.crate` archive is opt-in. Lockfile
strictness is also opt-in with `locked: true`; by default Cargo may resolve or refresh
the package lockfile during preflight.

After the crate already exists on crates.io, subsequent releases can use Trusted
Publishing without storing an API token:

```yaml
# .github/workflows/publish.yml
name: Publish Rust crate

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    permissions:
      contents: read
      id-token: write
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-publish.yml@v1
    with:
      package-name: rust-crate
      dry-run: false
      release-environment: release
```

On crates.io, configure the trusted publisher with the consuming repository, the
**caller workflow filename** (for example `publish.yml`), and the same environment
name (`release`). The reusable workflow requests a short-lived token through the
official crates.io OIDC action; it does not accept a stored crates.io token.

For a brand-new crate name, the first publication still has to establish ownership
before Trusted Publishing can be configured. After that first publish, configure the
trusted publisher and consider enabling crates.io's Trusted Publishing Only mode.

The reusable publish workflow defaults to `dry-run: true`, which runs only the release
preflight and requests no OIDC token. Live publishing is allowed
only from a GitHub Release event, a manual workflow dispatch, or a tag push. Protect
the caller's `release` environment with the approval rules appropriate to the repository.

GitHub Release assets can be prepared independently from crates.io publication:

```yaml
jobs:
  github-release:
    permissions:
      contents: write
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-github-release.yml@v1
    with:
      package-name: rust-crate
      tag-name: v0.1.0
      dry-run: false
      release-environment: release
```

The workflow reuses the release preflight, packages exactly one crate, generates and
verifies `SHA256SUMS`, and then attaches both the `.crate` archive and checksum file
to the GitHub Release. Generated release notes are enabled by default.

Live release creation requires an existing tag that matches the package version and
points at the commit the workflow packaged. It is limited to a push of that exact tag or
a manual workflow dispatch run from the tagged commit, and it never overwrites an existing
GitHub Release for the tag. The mutating job runs through the selected GitHub environment
with `contents: write`; dry-run mode only prepares and retains the checksummed release
assets.

GitHub checks the permissions of every job in a reusable workflow against the calling
job before it evaluates `if:` conditions. The calling job must therefore grant
`contents: write` for `rust-github-release.yml` and `id-token: write` for
`rust-publish.yml` even when `dry-run: true` skips the mutating job; otherwise the run
fails at startup without creating any jobs. The dry-run jobs themselves still request
read-only tokens. For pull-request verification that needs no elevated grant, call
`rust-release-preflight.yml` instead.

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
