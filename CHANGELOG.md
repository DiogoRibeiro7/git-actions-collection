# Changelog

All notable changes to this repository are documented here.

## Unreleased

### Deprecated

- `database-migration.yml`'s `flyway-license-key` secret. Pass `FLYWAY_LICENSE_KEY` instead, which `secrets: inherit` also provides.

### Fixed

- `terraform-plan-comment.yml` passed when `terraform plan` failed, because the plan was piped through `tee` without `pipefail`. The workflow now posts the plan output, including any error, and then fails the job.
- `changelog-auto-pr.yml` failed on every run: it installed git-cliff with `apt-get`, but Ubuntu does not package it. It now installs the git-cliff 2.14.2 release binary through the pinned `taiki-e/install-action`, which verifies its checksum.
- `python-test-matrix.yml` failed on Windows, which its default `os-matrix` includes: its steps are bash scripts, but Windows runners default to PowerShell. The job now runs its steps, including `test-command`, in bash on every OS, and the self-test covers Windows and macOS.
- `database-migration.yml` applied migrations even with `dry-run: true`: the Liquibase and Alembic dry runs printed the SQL and then ran it. Dry runs now skip the migration step. Flyway dry runs need a Flyway Teams license key.
- `lockfile-consistency.yml` failed for every Poetry project: it installed the latest Poetry and ran `poetry lock --check`, which Poetry 2 removed. It now runs `poetry check --lock` with Poetry pinned by a new `poetry-version` input (default `2.5.1`, matching `setup-poetry`) on Python 3.12 from `setup-python`.
- `database-migration.yml` could not start Flyway or Liquibase, because it moved only their launchers into `/usr/local/bin`, away from their libraries. Each tool now stays in its own directory on `PATH`.
- `pytorch-train-deploy.yml` could not start: it ran its CUDA container with `--gpus all` on `ubuntu-latest`, which has no GPU. GPU access is now opt-in through `gpu: true`, with a new `runs-on` input for GPU runners. The workflow no longer requests the unused `id-token: write`, its inputs are described, and the guide says the deploy step is a placeholder and drops a `pip-version` input that never existed.
- Security fix in the supported `security-scan.yml`: without `dependency-install-command`, pip-audit audited its own scanner environment instead of the caller's dependencies, so projects always passed. It now audits the root `requirements.txt`, or the dependencies `pyproject.toml` resolves to, and warns when there is nothing to audit. The scanner environments also lived in the workspace, so with the default `paths: .` Bandit scanned the scanners' own packages (55 findings in a clean project) and failed. They now live in `RUNNER_TEMP`. Expect real pip-audit findings where there were none.
- The documented `database-migration.yml` call passed per-environment secrets explicitly, which GitHub rejects because the workflow cannot declare them. The guide and example now use `secrets: inherit`.
- `docker-build-push.yml` (and `publish-docker-on-tag.yml` and `release-container.yml`, which call it) pushed the image before scanning it, so a failing Trivy scan could not stop a vulnerable image from being published. It now builds the first platform into the local Docker engine, scans that, and pushes only after the scan passes. Other platforms in a multi-platform build are not scanned.
- `ci-monorepo-matrix.yml` failed whenever more than one top-level folder changed, because it wrote the folder list to a step output over several lines. On pull requests it also diffed from the repository's first commit, so every folder ran. It now writes one line and compares pull requests with their base. `ci-monorepo-runner.yml` now lints a folder's own `.github/workflows` (it looked for the folder inside itself), fails on invalid Kubernetes manifests instead of ignoring them (custom resources without a schema are skipped), and runs `terraform validate` after `terraform init`.
- `infra-lint.yml` never failed and never linted: both linters ended in `|| true`, TFLint rejected the positional path it was given (dropped in TFLint 0.47), and cfn-lint was pointed at a directory, which it refuses. TFLint 0.64.0 (via the pinned `setup-tflint`) now checks each path recursively, cfn-lint 1.57.0 checks only the templates listed in the new `cloudformation-templates` input, and findings fail the job unless the new `soft-fail` input is true. The Checkov, tfsec and KICS steps, which were hard-coded off, are removed.

## 1.3.0 - 2026-09-25

### Added

- The supported `python-lint` composite action accepts an optional `working-directory` input (default `.`).
- New Rust workflows: `rust-coverage.yml` (cargo-llvm-cov with an optional LCOV artifact and line-coverage threshold), `rust-docs.yml` (rustdoc with warnings as errors), `rust-benchmark.yml` (short Criterion benchmark smoke runs), and `rust-release-preflight.yml` (checks package metadata and runs a verified `cargo package`).
- Experimental Rust release workflows: `rust-publish.yml` publishes to crates.io through Trusted Publishing (GitHub OIDC, no long-lived token), and `rust-github-release.yml` creates a GitHub Release with the verified `.crate` and a `SHA256SUMS` file. Both are dry runs unless the caller opts in and run the live job in a protected environment. `rust-release-preflight.yml` and `rust-publish.yml` accept a `packages` list to verify and publish selected workspace crates in order.
- `rust-security.yml` can enforce `cargo-deny` policies (`run-cargo-deny`, off by default) alongside `cargo-audit`.
- `SUPPORT.md` defines compatibility and deprecation rules for supported components. `.github/supported-interfaces.json` records their public interfaces, and CI fails when an interface changes without being recorded.
- A documentation site is published at https://diogoribeiro7.github.io/git-actions-collection/, built with MkDocs in strict mode from the repository's Markdown.

### Changed

- `release-drafter.yml` now runs release-drafter v7 (Node 24). Callers' `release-drafter.yml` configs can no longer use `autolabeler` (moved to the separate `release-drafter/release-drafter/autolabeler` action), `include-pre-releases` (use the `prerelease` and `prerelease-identifier` inputs), or `references` (use workflow `on:` filters). The workflow no longer passes the `GITHUB_TOKEN` environment variable, which v7 ignores in favour of its `token` input.
- Workflow token permissions are now explicit and job-scoped. `api-testing.yml`, `concurrency-caching.yml`, and `test-python-test-matrix.yml` declare `contents: read`; `canary-release.yml` and `multi-cloud-deploy.yml` grant write scopes only to the jobs that use them, and `multi-cloud-deploy.yml` no longer requests the unused `pull-requests: write`.
- `api-testing.yml` no longer opens GitHub issues for OWASP ZAP findings; the report remains available as the `zap_scan` artifact, and callers no longer need `issues: write`.
- Security compatibility change: Python actions and reusable workflows now default to pip `26.2.1`, replacing the vulnerable `24.3.1` installer. The new default requires Python 3.10 or newer; explicit `pip-version` overrides remain available. The supported-interface snapshot records this change under the security exception in `SUPPORT.md`.
- Security compatibility change: Node.js 20 reached end of life on 2026-04-30 and no longer receives security fixes, so Node.js defaults move to 24 (the active LTS). This changes the `node-version` default of the supported `setup-yarn` and `markdown-lint` actions and of `node-ci.yml`, `npm-publish.yml`, `publish-to-npm.yml`, `release.yml` and `vercel-nextjs.yml`, plus the fixed Node.js versions in `api-testing.yml`, `aws-lambda-deploy.yml`, `ci-monorepo-runner.yml`, `concurrency-caching.yml`, `security-scan.yml` and the workflow generator. Pass `node-version` to keep an older release. The supported-interface snapshot records this change under the security exception in `SUPPORT.md`.
- Updated the JavaScript test toolchain to patched Vitest 4, Vite 8, and ESLint 10, migrated ESLint configuration, and refreshed both Yarn lockfiles.
- Repository development tooling now requires Node.js 26+, and repository CI runs Node.js 26. Node.js 25+ no longer bundles Corepack, so CI installs Corepack 0.36.0 from npm.
- Updated Requests, Poetry, and pytest pins used by shell actions and examples, and raised the Python build-tool security floors.
- Raised the Django example's Django and Gunicorn minimum versions to patched releases.
- Added npm/example dependency updates to Dependabot and dependency auditing to repository CI.
- Promoted `rust-ci.yml`, `rust-quality.yml`, `rust-security.yml`, `rust-coverage.yml`, `rust-docs.yml`, `rust-benchmark.yml`, and `rust-release-preflight.yml` from reference to supported. Their interfaces are now covered by the v1 compatibility and deprecation policy in `SUPPORT.md`. `rust-publish.yml` and `rust-github-release.yml` remain experimental.
- `rust-ci.yml` rejects `all-features` combined with `no-default-features` or an explicit feature list, as the other Rust workflows already did.
- Workflows now use `actions/checkout` 7, which refuses to check out fork pull request code when the workflow is triggered by `pull_request_target` or `workflow_run`. Collection workflows called from those events can no longer build a fork's code.
- The third-party actions the collection uses now run on Node.js 24. Self-hosted runners need Actions Runner v2.327.1 or later.

### Fixed

- `pr-policy.yml` labels by changed paths only when the caller has a `.github/labeler.yml`, which must use the labeler v5+ match-object format; callers without one no longer fail. The repository's own labeler config uses the new format.
- `python-lint.yml`, `pr-policy.yml`, and `aws-lambda-deploy.yml` failed for every caller outside this repository: their `./.github/actions/...` steps resolved inside the caller's checkout. They now check out this collection at `job.workflow_sha`, the exact commit of the called workflow, and run the actions from there. `python-lint.yml` checks the caller's code out into `project/` and gains an optional `working-directory` input. `job.workflow_sha` is not available on GitHub Enterprise Server.
- `ci-monorepo-matrix.yml` called `ci-monorepo-runner.yml` from a step, which GitHub rejects; it now calls it as a job.
- Workflows and actions that run `corepack enable` failed on Node.js 25 and newer, which no longer bundle Corepack. `setup-yarn`, `node-ci.yml`, `npm-publish.yml`, `vercel-nextjs.yml`, `lockfile-consistency.yml` and `ci-monorepo-runner.yml` now install Corepack 0.36.0 from npm first when Node.js is 25 or newer, and keep the bundled Corepack on older releases.
- Some workflows pinned actions to SHAs that do not exist and failed when those steps ran: setup-go and setup-java in `aws-lambda-deploy.yml`, configure-aws-credentials in `multi-cloud-deploy.yml`, and rust-toolchain in `ci-monorepo-runner.yml`. The Rust step also lacked its required `toolchain` input and now uses `stable`. Each action is now pinned to one tagged release across the collection: setup-go 6.5.0, setup-java 6.0.1, setup-node 6.5.0, setup-python 6.3.0, configure-aws-credentials 6.3.0 (moved from 4.0.2, which ran on the retired Node 20 runtime), and checkout 7.0.1 in the examples and the workflow generator.
- Other pins were not release commits: azure/login and google-github-actions/auth in `multi-cloud-deploy.yml` and kics in `infra-lint.yml` pointed at SHAs that do not exist, and rust-cache, attest-build-provenance and crates-io-auth-action used untagged commits. They now use azure/login 3.1.0, auth 3.0.0, kics-github-action 2.1.20, rust-cache 2.9.2, attest-build-provenance 3.2.0 and crates-io-auth-action 1.0.5. CI runs `scripts/verify_action_pins.py` to check every pin against its repository's tags.
- Several reference workflows used action tags that do not exist, so they failed for every caller: `actions/checkout@5` in `pr-policy.yml`, `k8s-manifests-lint.yml` and `ci-monorepo-matrix.yml`, plus `hashicorp/setup-terraform@3`, `codelytv/pr-size-labeler@1` and `actions/labeler@6`. These refs and the remaining mutable ones, such as `@main`, `@v4` and `@stable`, now point at release commits, and a test rejects mutable refs.
- `codeql-analysis.yml` and `security-scan.yml` pinned `github/codeql-action` to the annotated tag object of the moving `v4` tag instead of a commit. They now use the v4.38.2 release commit.

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
