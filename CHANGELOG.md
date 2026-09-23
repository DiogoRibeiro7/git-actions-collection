# Changelog

All notable changes to this repository are documented here.

## 1.1.0 - 2026-09-23

### Added

- Added a post-v1 ecosystem expansion roadmap covering stronger workflow contracts, Rust, R, Ruby, Go, JVM, Node/TypeScript, scientific and LaTeX projects, release engineering, supply-chain controls, CI efficiency, and developer tooling.
- Added the optional `dependency-install-command` input to the supported `security-scan.yml` reusable workflow so callers can install their real dependency set before `pip-audit` runs.

### Changed

- `security-scan.yml` can now freeze the consumer project's resolved dependency closure before scanner tooling is installed and audit that captured set instead of only the runner environment.
- Updated the maintained security-scan example and contract tests for consumer dependency auditing.

## 1.0.0 - 2026-09-23

First stable release of the GitHub Actions collection.

### Stable support surface

- all 16 composite actions are covered by direct contract tests;
- `python-test-matrix.yml` and `security-scan.yml` are the initially supported reusable workflows;
- supported external action dependencies are pinned to immutable commit SHAs;
- supported workflows enforce explicit permissions and least-privilege defaults.

### Architecture

- `main` is the only permanent development branch;
- stable consumers use the moving `v1` tag or an exact commit SHA;
- repository releases are created manually through the dedicated release workflow;
- npm, PyPI, and container publishing each have one canonical reusable implementation with compatibility aliases for older entry points.

### Reliability and security

- repository validation is PR-first rather than repeated after every merge;
- supported reusable workflows have executable self-tests;
- release preflight validates the default branch, semantic version, metadata, and retired branch references before creating a tag;
- executable GitHub Actions dependencies were upgraded away from retired Node 16 and Node 20 runtimes where current Node 24-compatible releases are available.

### Compatibility

Reference and experimental workflows remain available in the v1 repository snapshot but are not covered by the same compatibility promise as supported components. See [SUPPORT.md](SUPPORT.md).
