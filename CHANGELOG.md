# Changelog

All notable changes to this repository are documented here.

## Unreleased

### Added

- The supported `python-lint` composite action accepts an optional `working-directory` input (default `.`).

### Changed

- `release-drafter.yml` now runs release-drafter v7 (Node 24). Callers' `release-drafter.yml` configs can no longer use `autolabeler` (moved to the separate `release-drafter/release-drafter/autolabeler` action), `include-pre-releases` (use the `prerelease` and `prerelease-identifier` inputs), or `references` (use workflow `on:` filters). The workflow no longer passes the `GITHUB_TOKEN` environment variable, which v7 ignores in favour of its `token` input.
- Workflow token permissions are now explicit and job-scoped. `api-testing.yml`, `concurrency-caching.yml`, and `test-python-test-matrix.yml` declare `contents: read`; `canary-release.yml` and `multi-cloud-deploy.yml` grant write scopes only to the jobs that use them, and `multi-cloud-deploy.yml` no longer requests the unused `pull-requests: write`.
- `api-testing.yml` no longer opens GitHub issues for OWASP ZAP findings; the report remains available as the `zap_scan` artifact, and callers no longer need `issues: write`.
- Security compatibility change: Python actions and reusable workflows now default to pip `26.2.1`, replacing the vulnerable `24.3.1` installer. The new default requires Python 3.10 or newer; explicit `pip-version` overrides remain available. The supported-interface snapshot records this change under the security exception in `SUPPORT.md`.
- Security compatibility change: Node.js 20 reached end of life on 2026-04-30 and no longer receives security fixes, so Node.js defaults move to 24 (the active LTS). This changes the `node-version` default of the supported `setup-yarn` and `markdown-lint` actions and of `node-ci.yml`, `npm-publish.yml`, `publish-to-npm.yml`, `release.yml` and `vercel-nextjs.yml`, plus the fixed Node.js versions in `api-testing.yml`, `aws-lambda-deploy.yml`, `ci-monorepo-runner.yml`, `concurrency-caching.yml`, `security-scan.yml` and the workflow generator. Pass `node-version` to keep an older release. The supported-interface snapshot records this change under the security exception in `SUPPORT.md`.
- Updated the JavaScript test toolchain to patched Vitest 4, Vite 8, and ESLint 10, migrated ESLint configuration, and refreshed both Yarn lockfiles.
- Repository development tooling now requires Node.js 26+, and repository CI runs Node.js 26. Node.js 25+ no longer bundles Corepack, so CI installs Corepack 0.36.0 from npm. Consumer workflow and action defaults are unchanged.
- Updated Requests, Poetry, and pytest pins used by shell actions and examples, and raised the Python build-tool security floors.
- Raised the Django example's Django and Gunicorn minimum versions to patched releases.
- Added npm/example dependency updates to Dependabot and dependency auditing to repository CI.

- Promoted `rust-ci.yml`, `rust-quality.yml`, `rust-security.yml`, `rust-coverage.yml`, `rust-docs.yml`, `rust-benchmark.yml`, and `rust-release-preflight.yml` from reference to supported. Their interfaces are now covered by the v1 compatibility and deprecation policy in `SUPPORT.md`. `rust-publish.yml` and `rust-github-release.yml` remain experimental.

### Fixed

- `pr-policy.yml` labels by changed paths only when the caller has a `.github/labeler.yml`, which must use the labeler v5+ match-object format; callers without one no longer fail. The repository's own labeler config uses the new format.
- `python-lint.yml`, `pr-policy.yml`, and `aws-lambda-deploy.yml` failed for every caller outside this repository: their `./.github/actions/...` steps resolved inside the caller's checkout. They now check out this collection at `job.workflow_sha`, the exact commit of the called workflow, and run the actions from there. `python-lint.yml` checks the caller's code out into `project/` and gains an optional `working-directory` input. `job.workflow_sha` is not available on GitHub Enterprise Server.
- `ci-monorepo-matrix.yml` called `ci-monorepo-runner.yml` from a step, which GitHub rejects; it now calls it as a job.
- Workflows and actions that run `corepack enable` failed on Node.js 25 and newer, which no longer bundle Corepack. `setup-yarn`, `node-ci.yml`, `npm-publish.yml`, `vercel-nextjs.yml`, `lockfile-consistency.yml` and `ci-monorepo-runner.yml` now install Corepack 0.36.0 from npm first when Node.js is 25 or newer, and keep the bundled Corepack on older releases.
- Some workflows pinned actions to SHAs that do not exist and failed when those steps ran: setup-go and setup-java in `aws-lambda-deploy.yml`, configure-aws-credentials in `multi-cloud-deploy.yml`, and rust-toolchain in `ci-monorepo-runner.yml`. The Rust step also lacked its required `toolchain` input and now uses `stable`. Each action is now pinned to one tagged release across the collection: setup-go 6.5.0, setup-java 6.0.1, setup-node 6.5.0, setup-python 6.3.0, configure-aws-credentials 6.3.0 (moved from 4.0.2, which ran on the retired Node 20 runtime), and checkout 7.0.1 in the examples and the workflow generator.

## 1.2.1 - 2026-09-23

### Fixed

- Fixed the supported `security-scan.yml` workflow invoking pip-audit 2.9.0 and Bandit 1.8.6 with unsupported SARIF output flags.
- Python scanners now emit their supported JSON formats and the workflow converts those reports to SARIF before GitHub code-scanning upload.
- Scanner tools are installed in an isolated temporary virtual environment so pinned scanner versions no longer mutate the consumer project's environment.
- Python scanner exit codes are captured so SARIF reports and artifacts are produced before the workflow fails on findings or scanner errors.

## 1.2.0 - 2026-09-23

### Added

- Added the optional `bandit-args` input to the supported `security-scan.yml` reusable workflow so consumers can preserve their own Bandit severity, confidence, and CLI policy while keeping the existing `-ll -ii` default unchanged.
- Expanded the reference Rust CI workflow with configurable feature sets and compatibility matrices, together with additional example and contract coverage.

### Changed

- Restored readable multi-line shell formatting in the Python dependency-audit path of `security-scan.yml`.
- Updated the maintained security-scan example and documentation to show explicit Bandit argument control.
- Updated Rust CI tests, example metadata, documentation, and roadmap progress for the new compatibility inputs.

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
