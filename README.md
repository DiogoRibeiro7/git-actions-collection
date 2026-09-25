# GitHub Actions Collection

[![Release](https://img.shields.io/github/v/release/DiogoRibeiro7/git-actions-collection)](https://github.com/DiogoRibeiro7/git-actions-collection/releases)
[![Docs](https://github.com/DiogoRibeiro7/git-actions-collection/actions/workflows/docs.yml/badge.svg?branch=main)](https://diogoribeiro7.github.io/git-actions-collection/)
[![Licence: MIT](https://img.shields.io/github/license/DiogoRibeiro7/git-actions-collection)](https://github.com/DiogoRibeiro7/git-actions-collection/blob/main/LICENSE)

Reusable GitHub Actions workflows and composite actions for Python, Rust, R,
JavaScript and infrastructure projects. Every third-party action is pinned to a
release commit, every workflow declares least-privilege permissions, and the
automation is tested like code.

**[Documentation](https://diogoribeiro7.github.io/git-actions-collection/)** ·
**[Catalogue](https://diogoribeiro7.github.io/git-actions-collection/catalogue/)** ·
[Changelog](CHANGELOG.md) · [Support policy](SUPPORT.md)

## Quick start

Call a reusable workflow as a job:

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  tests:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/python-test-matrix.yml@v1
    with:
      python-versions: '["3.12", "3.13"]'
```

Or use a composite action as a step:

```yaml
steps:
  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
  - uses: DiogoRibeiro7/git-actions-collection/.github/actions/python-lint@v1
    with:
      enable-mypy: true
```

`@v1` follows every compatible release. Pin an exact commit SHA instead when you
need a fully reproducible build, and always for experimental workflows. Each
workflow's page in the [catalogue](https://diogoribeiro7.github.io/git-actions-collection/catalogue/)
lists its inputs, outputs, secrets and the permissions the calling job must grant.

## Supported components

These components are covered by the v1 compatibility promise: their inputs,
outputs, secrets and required permissions only change compatibly within `v1`.

| Reusable workflow | What it does |
| --- | --- |
| [`python-test-matrix.yml`](.github/workflows/python-test-matrix.yml) | Runs pytest across Python versions and operating systems. |
| [`security-scan.yml`](.github/workflows/security-scan.yml) | Runs pip-audit, Bandit and optional Trivy scans, uploads SARIF and attests the reports. |
| [`rust-ci.yml`](.github/workflows/rust-ci.yml) | Runs cargo fmt, check, Clippy and tests, with an optional toolchain and OS matrix. |
| [`rust-quality.yml`](.github/workflows/rust-quality.yml) | Runs cargo fmt and Clippy as a fast quality gate. |
| [`rust-security.yml`](.github/workflows/rust-security.yml) | Audits dependencies with cargo-audit and optional cargo-deny policies. |
| [`rust-coverage.yml`](.github/workflows/rust-coverage.yml) | Measures coverage with cargo-llvm-cov, with an LCOV artifact and optional threshold. |
| [`rust-docs.yml`](.github/workflows/rust-docs.yml) | Builds rustdoc with warnings treated as errors. |
| [`rust-benchmark.yml`](.github/workflows/rust-benchmark.yml) | Runs a short Criterion benchmark smoke test. |
| [`rust-release-preflight.yml`](.github/workflows/rust-release-preflight.yml) | Checks crate metadata and runs a verified `cargo package` before release. |

| Composite action | What it does |
| --- | --- |
| [`python-lint`](.github/actions/python-lint) | Runs Ruff and, optionally, mypy. |
| [`python-type-check`](.github/actions/python-type-check) | Runs mypy after installing optional requirements. |
| [`check-imports`](.github/actions/check-imports) | Compares a project's imports with its declared dependencies. |
| [`setup-poetry`](.github/actions/setup-poetry) | Installs Poetry with dependency caching. |
| [`benchmark-smoke`](.github/actions/benchmark-smoke) | Runs pytest-benchmark and keeps the results. |
| [`aws-lambda-build`](.github/actions/aws-lambda-build) | Packages a Python Lambda deployment archive. |
| [`smart-dependency-update`](.github/actions/smart-dependency-update) | Plans, and optionally applies, dependency updates across several manifest formats, flagging conflicts. |
| [`setup-r`](.github/actions/setup-r) | Installs R and optional CRAN packages. |
| [`r-lint`](.github/actions/r-lint) | Lints R sources with lintr. |
| [`r-testthat`](.github/actions/r-testthat) | Runs testthat or `devtools::test()`. |
| [`setup-yarn`](.github/actions/setup-yarn) | Enables Corepack and installs Yarn dependencies with caching. |
| [`markdown-lint`](.github/actions/markdown-lint) | Lints Markdown with markdownlint-cli. |
| [`gradle-build`](.github/actions/gradle-build) | Runs a Gradle build with caching. |
| [`secret-scan`](.github/actions/secret-scan) | Scans the repository for leaked secrets with gitleaks. |
| [`pr-template-enforcer`](.github/actions/pr-template-enforcer) | Fails pull requests whose description misses required sections. |
| [`apm-integration`](.github/actions/apm-integration) | Sends deployment events and metrics to Datadog, New Relic or Azure Application Insights. |

The [catalogue](https://diogoribeiro7.github.io/git-actions-collection/catalogue/)
also lists the reference and experimental workflows for Node.js, Go, Java, .NET,
Ruby, Deno, containers, Terraform, cloud deployment and publishing.

## Support tiers

- **Supported:** compatible within `v1`, with behavioural tests and a recorded
  interface. Breaking changes need a new major version.
- **Reference:** useful and tested statically, but without the compatibility
  promise yet. Pin a commit SHA if you depend on details.
- **Experimental:** publishing, deployment and other environment-dependent
  workflows that have not earned `v1` status. Pin a commit SHA.

[SUPPORT.md](SUPPORT.md) defines the tiers, the promotion criteria and the
deprecation policy.

## Security

- Third-party actions are pinned to the commit of a release tag, and CI checks
  every pin against the action's tags.
- Each workflow declares the permissions it needs, and its reference page
  shows what the calling job must grant.
- Publishing and deployment workflows use OIDC and GitHub environments rather
  than long-lived secrets where the target supports it.

Review a workflow's permissions, secrets and environments before you adopt it.

## Versioning and releases

Releases follow semantic versioning. Each release gets an immutable tag such as
`v1.3.0`, and the moving `v1` tag advances to the latest compatible release. The
collection is used straight from GitHub; it is not published to the Marketplace
or a package registry. See [RELEASES.md](RELEASES.md) and the
[changelog](CHANGELOG.md).

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md) covers setup (Python 3.10+, Node.js 26+ and
Bats), the test layers, and how to change a supported interface. Changes to a
workflow or action should come with a test or an executable example.

## Licence

MIT. See [LICENSE](LICENSE).
