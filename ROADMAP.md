# Roadmap

This roadmap describes the next development areas for `git-actions-collection` after the stable v1 baseline.

It is a priority map rather than a delivery calendar. Work should land through pull requests against `main`, and stable consumers should continue to use the moving `@v1` tag or an exact commit SHA.

## Engineering principles

New reusable automation should remain small, composable, and testable rather than growing into large all-purpose workflows.

A workflow or composite action should normally reach the supported tier only when it has:

- executable regression or contract coverage;
- a minimal consumer example;
- documented inputs, outputs, secrets, and permissions;
- least-privilege permissions;
- pinned third-party actions where practical;
- predictable failure behaviour and useful job summaries;
- a migration or deprecation path when its public interface changes.

The collection should also avoid unnecessary GitHub Actions usage. Expensive matrices, scheduled jobs, deployment checks, and duplicate post-merge runs should only exist when they add clear value.

## Current baseline

The repository already contains a broad workflow catalogue, but the stable compatibility surface is intentionally smaller.

At the current v1 baseline:

- `python-test-matrix.yml` and `security-scan.yml` are supported reusable workflows;
- Rust, Ruby, Go, Java, Node, .NET, Deno, infrastructure, publishing, and repository-governance workflows exist mainly as reference or experimental components;
- reusable composite actions already cover Python, R, dependency inspection, repository policy, security scanning, AWS packaging, and common setup tasks.

The next stage is therefore not simply to add more YAML. It is to promote useful workflows into well-tested, reusable products and fill the missing ecosystem-specific gaps.

---

## Priority 0 — Strengthen the reusable-workflow platform

Before expanding the catalogue aggressively, improve the guarantees around every public workflow.

- [ ] Add contract tests for every workflow intended to become supported.
- [ ] Add smoke-test consumer repositories or fixtures for each supported ecosystem.
- [ ] Validate workflow syntax and semantics with dedicated GitHub Actions linters.
- [ ] Add checks for overly broad `permissions` blocks.
- [ ] Detect mutable or unpinned third-party action references.
- [ ] Keep `.github/support-matrix.yml`, documentation, examples, and release metadata consistent automatically.
- [ ] Add a formal deprecation policy for supported workflow inputs and outputs.
- [ ] Add compatibility tests that fail when a supported public interface changes unexpectedly.
- [ ] Extend release preflight checks to validate the complete supported surface.
- [ ] Add a consumer-reference audit to find stale examples and outdated `@main` or obsolete repository references.

### Migration tooling

- [ ] Extend `migrate_starter_workflows.py` beyond Python and Node.
- [ ] Detect Rust, R, Ruby, Go, Java, .NET, and common JavaScript package-manager configurations.
- [ ] Add a dry-run mode that explains the proposed migration without changing files.
- [ ] Produce machine-readable migration reports.
- [ ] Add migration fixtures and regression tests for every supported ecosystem.

---

## Priority 1 — Rust as a first-class supported ecosystem

The repository already contains `rust-ci.yml`, but it is currently a reference workflow and only performs formatting, `cargo check`, and Clippy. Rust should become a complete supported surface.

### Core CI

- [x] Add configurable Rust toolchain inputs.
- [x] Add `cargo test` support.
- [x] Support workspaces and configurable feature sets.
- [x] Support `--all-features`, `--no-default-features`, and explicit feature lists.
- [x] Add optional Linux, macOS, and Windows matrices.
- [x] Add stable, beta, nightly, and MSRV testing where requested by the consumer.
- [x] Add dependency and build caching without making cache correctness part of the build result.
- [x] Add Rust example projects and contract tests.
- [ ] Promote the core Rust workflow from reference to supported after the acceptance criteria are met.

### Rust quality and security

- [x] Add a reusable Rust quality workflow for `rustfmt` and Clippy.
- [x] Add `cargo-audit` vulnerability scanning.
- [x] Add `cargo-deny` checks for advisories, licences, bans, and duplicate dependency policy.
- [ ] Add `cargo-llvm-cov` coverage reporting.
- [ ] Add documentation builds with warnings treated as errors.
- [ ] Add optional benchmark smoke checks for Criterion-based projects.

### Rust releases

- [ ] Validate package metadata before release.
- [ ] Run `cargo package` as a release preflight.
- [ ] Add crates.io publication with protected release environments and the safest available authentication mechanism.
- [ ] Generate GitHub Releases with checksums and release notes.
- [ ] Support workspace crates without forcing every crate to publish.

---

## Priority 2 — Promote the other language ecosystems

### R

- [ ] Turn the existing internal R checks into a reusable public `R CMD check` workflow.
- [ ] Add configurable R-version and operating-system matrices.
- [ ] Add public `lintr` and `testthat` orchestration workflows around the existing composite actions.
- [ ] Add coverage reporting.
- [ ] Add package-build checks and documentation generation for package projects.
- [ ] Add examples for statistical packages and research repositories.

### Ruby

- [ ] Add RuboCop quality checks.
- [ ] Add `bundler-audit` security checks.
- [ ] Validate gem builds before release.
- [ ] Add RubyGems publishing as a protected release workflow.
- [ ] Add configurable operating-system matrices where native-extension testing requires them.
- [ ] Add contract coverage and promote `ruby-ci.yml` from reference to supported.

### Go

- [ ] Expand `go-ci.yml` with configurable Go-version matrices.
- [ ] Add `gofmt`, `go vet`, and static-analysis gates.
- [ ] Add `govulncheck`.
- [ ] Add race-detector and coverage options.
- [ ] Add reusable release builds for common platform/architecture targets.

### Java and JVM

- [ ] Support both Gradle and Maven consumers.
- [ ] Add JDK-version matrices.
- [ ] Add test, formatting, static-analysis, and dependency-security gates.
- [ ] Add package/release workflows for JVM libraries.
- [ ] Reuse the existing `gradle-build` composite where appropriate.

### Node.js and TypeScript

- [ ] Support npm, Yarn, and pnpm consistently.
- [ ] Add Node-version matrices.
- [ ] Standardise lint, type-check, unit-test, and build stages.
- [ ] Add package-manager-aware caching.
- [ ] Harden npm publishing and provenance checks.
- [ ] Add reusable TypeScript library and application examples.

### .NET and Deno

- [ ] Add contract tests for the existing reference workflows.
- [ ] Add configurable runtime/version matrices.
- [ ] Add formatting, testing, coverage, and dependency-security checks.
- [ ] Promote workflows only after real consumer examples pass end-to-end.

---

## Priority 3 — Scientific, data, documentation, and academic workflows

The collection should support research and technical-writing repositories as deliberately as application repositories.

### Scientific Python and notebooks

- [ ] Add notebook linting and execution checks.
- [ ] Add deterministic notebook/research smoke tests.
- [ ] Validate that notebooks are reproducible from declared dependencies.
- [ ] Add optional notebook-output stripping checks.
- [ ] Add scientific-package build/test templates distinct from application CI.

### LaTeX and academic material

- [ ] Add reusable LaTeX build workflows.
- [ ] Support multi-file projects with a canonical root document.
- [ ] Cache TeX dependencies where safe.
- [ ] Upload generated PDFs as build artifacts.
- [ ] Add optional bibliography and reference validation.
- [ ] Add a smoke-test example for academic presentations and papers.

### Documentation and static sites

- [ ] Add MkDocs build and link validation.
- [ ] Add Jekyll build and link validation.
- [ ] Add Quarto documentation builds.
- [ ] Add spelling and Markdown quality gates as optional checks.
- [ ] Add GitHub Pages deployment workflows using protected, explicit permissions.
- [ ] Add documentation-preview workflows for pull requests where practical.

---

## Priority 4 — Security and software supply chain

Build on the existing `security-scan.yml`, CodeQL, dependency-review, and secret-scanning components.

- [ ] Add SBOM generation for packages and containers.
- [ ] Add artifact provenance/attestation support to release workflows.
- [ ] Add licence-policy validation.
- [ ] Add repository-wide third-party action pinning checks.
- [ ] Add reusable workflow-permission audits.
- [ ] Add workflow-security linting.
- [ ] Add container image vulnerability scanning.
- [ ] Add signed-container and checksum verification patterns.
- [ ] Add optional OpenSSF-style repository security checks.
- [ ] Add release-environment validation for privileged publishing workflows.

---

## Priority 5 — Release engineering

Create a consistent release layer across ecosystems instead of maintaining unrelated publishing workflows.

- [ ] Standardise release preflight behaviour.
- [ ] Add reusable GitHub Release creation.
- [ ] Generate checksums for release artifacts.
- [ ] Generate or validate changelogs.
- [ ] Support semantic-version validation without forcing semantic-release on every repository.
- [ ] Add release workflows for PyPI, crates.io, RubyGems, npm, containers, and generic binaries.
- [ ] Separate build, verification, and publication so consumers can insert manual approval.
- [ ] Add protected-environment examples for release jobs.
- [ ] Add rollback/recovery documentation for failed partial releases.
- [ ] Add release contract tests that never publish real artifacts.

---

## Priority 6 — CI efficiency and observability

The collection should help reduce Actions minutes as well as add checks.

- [ ] Expand path-aware execution for monorepos.
- [ ] Add reusable changed-files detection.
- [ ] Add matrix pruning for unaffected packages or platforms.
- [ ] Standardise concurrency and cancellation of superseded pull-request runs.
- [ ] Improve dependency-cache reuse while preserving deterministic installs.
- [ ] Add artifact-retention defaults appropriate to artifact type.
- [ ] Add workflow run summaries with key test, coverage, lint, and release results.
- [ ] Add optional CI-duration reporting.
- [ ] Add an audit that identifies redundant or duplicate workflows in consumer repositories.
- [ ] Document when scheduled workflows are justified and when they should be avoided.

---

## Priority 7 — Repository governance and maintenance

- [ ] Add repository-health checks for required metadata and community files.
- [ ] Validate CODEOWNERS syntax where present.
- [ ] Validate pull-request and issue templates.
- [ ] Add conventional-commit enforcement as an opt-in supported workflow.
- [ ] Add changelog and release-note policy checks.
- [ ] Add stale-reference and broken-link detection.
- [ ] Add licence-file and package-metadata consistency checks.
- [ ] Add configurable dependency-update policy checks.
- [ ] Add repository settings audit tooling without automatically changing protected settings.
- [ ] Keep merge and release decisions explicit; do not introduce unconditional auto-merge automation.

---

## Priority 8 — Containers, infrastructure, and deployment

Existing deployment workflows should remain experimental until they have strong safety boundaries and realistic test coverage.

### Containers

- [ ] Harden multi-platform Docker build workflows.
- [ ] Add reproducible metadata, labels, SBOMs, provenance, and vulnerability scans.
- [ ] Separate container build/test from publication.
- [ ] Add registry-agnostic examples.

### Infrastructure

- [ ] Separate Terraform format/validate, plan, and apply workflows.
- [ ] Keep apply operations behind protected environments and explicit permissions.
- [ ] Expand OIDC-first cloud authentication examples for AWS, Azure, and GCP.
- [ ] Add policy/static checks for Terraform and Kubernetes manifests.
- [ ] Harden Helm lint/test workflows.
- [ ] Add deployment smoke-test hooks without coupling them to a specific cloud provider.

---

## Priority 9 — Developer experience

Make the collection easier to adopt without hiding what it generates.

- [ ] Expand `workflow_generator.py` to cover the supported ecosystem matrix.
- [ ] Auto-detect repository manifests and propose suitable workflows.
- [ ] Generate minimal consumer YAML that delegates to reusable workflows.
- [ ] Add a dry-run/explain mode showing exactly what will be generated.
- [ ] Add example configurations for common project types.
- [ ] Add a compatibility checker for consumer inputs against the selected collection version.
- [ ] Add machine-readable metadata describing workflow inputs, outputs, secrets, and support tier.
- [ ] Generate parts of the documentation catalogue from that metadata to reduce drift.

---

## Candidate project templates

As the supported workflows mature, maintain executable example projects for:

- [ ] Python library;
- [ ] scientific Python package;
- [ ] R package;
- [ ] Rust crate;
- [ ] Ruby gem;
- [ ] Go library or CLI;
- [ ] Java/Gradle library;
- [ ] Node/TypeScript library;
- [ ] .NET library;
- [ ] LaTeX academic project;
- [ ] MkDocs/Jekyll documentation site;
- [ ] Dockerised service;
- [ ] small monorepo.

Each example should act as a consumer contract, not merely as documentation.

## Promotion criteria

A reference or experimental component can move to `supported` when:

1. its public interface is documented;
2. its permissions and secrets are explicit;
3. executable tests cover normal operation and important failures;
4. at least one consumer example exercises it;
5. its third-party dependencies are pinned and reviewed;
6. repository contract tests protect its public path and usage;
7. it has a clear compatibility and deprecation story.

This keeps the stable surface smaller than the catalogue, but substantially more trustworthy.
