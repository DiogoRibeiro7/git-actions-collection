# GitHub Actions Collection

A curated library of reusable GitHub Actions, workflows, and helpers maintained by Diogo Ribeiro (ESMAD — Instituto Politécnico do Porto).
This repository stores a collection of reusable GitHub Actions, and the goal is to centralize workflows, composite actions, and utilities so they can be shared across multiple projects.

## Repository overview

- **Composite actions** for Python, Java, Node.js, R, Gradle, security scanning, dependency governance, and environment setup stored in `.github/actions/`.
- **Reusable workflows** covering CI for popular stacks, artifact publishing, infrastructure automation, security checks, and release orchestration in `.github/workflows/`.
- **Reference documentation** for the most feature-rich workflows under `docs/` with step-by-step usage notes and configuration guides.
- **Example projects** in `examples/` demonstrating how to consume the composite actions and workflows in real repositories.
- **Utility scripts and tests** in `scripts/` and `tests/` to keep the collection up to date and verifiable.

## Directory layout

| Path | Purpose |
| --- | --- |
| `.github/actions/` | Composite actions written in YAML that can be consumed from any repository. |
| `.github/workflows/` | Reusable workflows invokable through `workflow_call` plus local automation for this repository. |
| `docs/` | Extended documentation for complex workflows (API testing, multi-cloud deploy, PyPI trusted publishing, etc.). |

## Testing

Run the full suite locally:

```
yarn test
pytest -q
bats tests/bash
```

For more details (single test file, env vars, mocks), see CONTRIBUTING.md.
| `examples/` | Sample repositories showcasing how to wire the actions and workflows together. |
| `scripts/` | Python utilities used by composite actions and migration helpers. |
| `tests/` | Pytest suite covering helper scripts and workflow generators. |
| `requirements-dev.txt` | Development dependencies required to run scripts and tests locally. |

Example layout:

```text
.github/
 ├── actions/
 │    ├── lint-python/
 │    │    └── action.yml
 │    └── check-imports/
 │         └── action.yml
 └── workflows/
      ├── release.yml
      └── security-scan.yml
```

---

## 🚀 Getting started

### Reuse a workflow from this collection

Call any reusable workflow directly from another repository via the `uses:` keyword:

```yaml
name: Reuse Example

on:
  push:
    branches: [ main ]

jobs:
  call-workflow:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/release.yml@main
```

### Invoke a composite action

Reference a composite action inside an existing workflow:

```yaml
steps:
  - uses: actions/checkout@v4
  - name: Check Imports
    uses: DiogoRibeiro7/gh-actions-collection/.github/actions/check-imports@main
```

> **Tip:** Replace `@main` with a tagged release for reproducible pipelines.

### Local development

This repository includes helper scripts and example workflows that rely on a small Python toolchain.
Install the development requirements in an isolated environment before running the utilities or the test suite:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Run the automated checks locally with:

```bash
pytest
```

The [`scripts/migrate_starter_workflows.py`](scripts/migrate_starter_workflows.py) CLI uses PyYAML to parse GitHub workflow manifests.
Installing the development dependencies ensures the converter and its tests run successfully.

## Documentation & examples

Each complex workflow is paired with a dedicated guide under `docs/`, and the `examples/` directory contains minimal repositories ready to copy-paste into your projects:

- API testing contract checks (`docs/api-testing.md`, `examples/api-testing/`)
- Multi-cloud infrastructure deployments (`docs/multi-cloud-deploy.md`, `examples/multi-cloud-deploy/`)
- Trusted PyPI releases (`docs/pypi-trusted-publishing.md`, `examples/python-package/`)
- Smart dependency management (`docs/smart-dependency-update.md`, `examples/smart-dependency-update/`)
- Vercel Next.js deployments (`docs/vercel-nextjs.md`)

Browse the remaining guides for workflows covering artifact management, database migrations, Deno projects, PyTorch training, and more.

## Security

The `security-scan` workflow audits Python dependencies and runs static analysis.
It uploads SARIF results to GitHub code scanning and saves them as build artifacts while retaining least privilege.

```yaml
permissions:
  contents: read
  security-events: write
  id-token: write
  attestations: write

jobs:
  scan:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/security-scan.yml@main
```

For a full example see [`examples/python-package/.github/workflows/security.yml`](examples/python-package/.github/workflows/security.yml).

Additional security helpers:

* [`secret-scan`](.github/actions/secret-scan) composite action runs gitleaks to block secret leaks.
* [`codeql-analysis`](.github/workflows/codeql-analysis.yml) workflow runs CodeQL for Python, JavaScript, and Go.
* [`dependency-review`](.github/workflows/dependency-review.yml) workflow warns about vulnerable dependency changes.
* [`multi-cloud-deploy`](.github/workflows/multi-cloud-deploy.yml) workflow deploys Terraform, Pulumi, or Bicep stacks to AWS, Azure, and GCP with OIDC authentication, drift detection, and cost estimates.
* [`apm-integration`](.github/actions/apm-integration) composite action sends deployment events and custom metrics to Datadog, New Relic, or Application Insights.
* [`artifact-management`](.github/workflows/artifact-management.yml) workflow cleans stale build artifacts, package versions, and container images.

## Composite actions (quick reference)

| Action | Path | Inputs & outputs | Summary |
| --- | --- | --- | --- |
| APM Integration | `.github/actions/apm-integration` | Required inputs: `provider`, `api-key`; optional: `app-id`, `environment`, `deployment-id`, `metrics-file`. | Sends deployment markers and optional custom metrics to Datadog, New Relic, or Azure Application Insights. |
| AWS Lambda Build (Python) | `.github/actions/aws-lambda-build` | Optional inputs: `src`, `output-zip`, `python-version`, `pip-version`. | Packages a Python Lambda with dependency vendoring and reproducible ZIP output. |
| Benchmark Smoke | `.github/actions/benchmark-smoke` | Optional inputs: `python-version`, `working-directory`, `pytest-args`, `pip-version`. | Runs `pytest-benchmark`, captures JSON output, and uploads the results as an artifact. |
| Check Imports vs pyproject | `.github/actions/check-imports` | Optional inputs: `paths`, `fail-on`, `format`, `update-pyproject`, `create-pr`, `pr-branch`, `python-version`, `pip-version`, `smart-update`. | Compares imports to `pyproject.toml`, optionally amends dependencies, and can open PRs with fixes. |
| Gradle Build | `.github/actions/gradle-build` | Optional inputs: `java-version`, `tasks`, `gradle-args`, `working-directory`. | Executes Gradle tasks with setup-java and setup-gradle caching support. |
| Markdown Lint | `.github/actions/markdown-lint` | Optional inputs: `paths`, `config-file`, `node-version`. | Installs `markdownlint-cli` and enforces Markdown conventions. |
| PR Template Enforcer | `.github/actions/pr-template-enforcer` | No inputs. | Fails a workflow if pull requests omit required summary and testing sections. |
| Python Lint & Type Check | `.github/actions/python-lint` | Optional inputs: `python-version`, `enable-mypy`, `pip-version`. | Runs Ruff linting and optionally mypy with pip caching. |
| Python Type Check | `.github/actions/python-type-check` | Optional inputs: `python-version`, `working-directory`, `requirements-file`, `extra-dependencies`, `mypy-args`, `pip-version`. | Installs dependencies and executes mypy across a repository or subdirectory. |
| R Lint | `.github/actions/r-lint` | Optional inputs: `r-version`, `cran-mirror`, `use-public-rspm`, `targets`, `config-file`, `additional-packages`, `working-directory`. | Provisions R (via `setup-r`) and runs `lintr` against provided targets. |
| R Testthat | `.github/actions/r-testthat` | Optional inputs: `r-version`, `cran-mirror`, `use-public-rspm`, `test-directory`, `install-dependencies`, `additional-packages`, `working-directory`, `use-devtools`. | Installs dependencies and runs `testthat` or `devtools::test()` suites. |
| Secret Scan | `.github/actions/secret-scan` | Optional input: `args`. | Wraps the official `gitleaks` action to scan repositories for leaked credentials. |
| Setup Poetry (with cache) | `.github/actions/setup-poetry` | Optional inputs: `python-version`, `install-deps`, `pip-version`. | Installs Poetry, primes pip/Poetry caches, and optionally runs `poetry install`. |
| Setup R Environment | `.github/actions/setup-r` | Optional inputs: `r-version`, `cran-mirror`, `use-public-rspm`, `packages`, `working-directory`. | Installs R with optional package bootstrapping and RSPM acceleration. |
| Setup Yarn (Corepack) | `.github/actions/setup-yarn` | Optional inputs: `node-version`, `working-directory`. | Enables Corepack, caches Yarn artifacts, and runs `yarn install --immutable` when a lockfile exists. |
| Smart Dependency Update | `.github/actions/smart-dependency-update` | Required input: `manifests`; optional: `apply`, `batch-size`, `dependabot`, `repo`, `github-token`, `pip-version`. Outputs: `report`. | Batches dependency upgrades, optionally consults Dependabot alerts, and emits a JSON report. |

> **Python tooling upgrade policy:** Python-based composite actions default to the latest pip release that has been validated in this repository (`24.3.1`). Consumers can override the `pip-version` input (set it to `latest` to follow upstream automatically) and upgrades are reviewed quarterly or when security advisories require it. Each release bump is tested in CI before updating the default to prevent supply-chain breakages.

## Reusable workflows (quick reference)

### CI and quality gates

| Workflow | Path | Requirements | Summary |
| --- | --- | --- | --- |
| API Testing | `.github/workflows/api-testing.yml` | Inputs: `openapi-spec`, `contract-path`, `base-url`; Secrets: —. | Validates OpenAPI specs, runs Postman or Pact contract checks, and optionally executes k6 load tests, GraphQL linting, and OWASP ZAP scans (`contract-type`, `load-script`, `graphql-schema`, `auth-command`, `run-zap`, `zap-token`). |
| CI Monorepo by Path | `.github/workflows/ci-monorepo-matrix.yml` | Inputs: `groups`; Secrets: —. | Splits monorepos into path-based job groups by delegating to other reusable workflows. |
| Concurrency and Caching Template | `.github/workflows/concurrency-caching.yml` | Inputs: —; Secrets: —. | Starter template demonstrating default permissions, concurrency groups, and cache sharing patterns. |
| Deno CI | `.github/workflows/deno-ci.yml` | Inputs: —; Secrets: —. | Lints, formats, and tests Deno apps with optional matrix (`deno-version`, `os-matrix`) and deploy support (`deploy`, `project`, `deno-deploy-token`). |
| .NET CI | `.github/workflows/dotnet-ci.yml` | Inputs: —; Secrets: —. | Restores, builds, and tests .NET solutions with configurable SDKs, frameworks, and test toggles. |
| Go CI | `.github/workflows/go-ci.yml` | Inputs: —; Secrets: —. | Performs Go module linting, testing, and coverage with configurable Go versions. |
| Java CI | `.github/workflows/java-ci.yml` | Inputs: —; Secrets: —. | Builds and tests Maven or Gradle projects with configurable build tool selection. |
| Node CI | `.github/workflows/node-ci.yml` | Inputs: —; Secrets: —. | Handles npm/Yarn install, lint, and test jobs with optional OS/Python matrices. |
| Python Lint | `.github/workflows/python-lint.yml` | Inputs: `python-version`, `enable-mypy`, `pip-version`; Secrets: —. | Wraps the composite Python lint action with configurable Python version, pip bootstrap, and mypy toggle. |
| Python Test Matrix | `.github/workflows/python-test-matrix.yml` | Inputs: `python-versions`, `os-matrix`, `test-command`, `pip-version`; Secrets: —. | Executes tests across custom OS and Python matrices with governed pip upgrades and supports arbitrary test commands. |
| PyTorch Train and Deploy | `.github/workflows/pytorch-train-deploy.yml` | Inputs: —; Secrets: —. | Trains PyTorch models, publishes artifacts, optionally benchmarks/deploys, and can push to MLflow (`hf-token`, `deploy`, `mlflow-uri`). |
| Ruby CI | `.github/workflows/ruby-ci.yml` | Inputs: —; Secrets: —. | Bundles, lints, and tests Ruby projects with multi-version matrices and optional Rubygems auth (`rubygems-token`). |
| Rust CI | `.github/workflows/rust-ci.yml` | Inputs: —; Secrets: —. | Builds, tests, and runs `clippy`, `fmt`, and `cargo audit` with sensible caching defaults. |
| Coverage Report | `.github/workflows/coverage-report.yml` | Inputs: `python-version`, `test-command`, `pip-version`; Secrets: —. | Runs Python tests and publishes HTML coverage artifacts with configurable interpreter, pip bootstrap, and test command. |
| Canary Release | `.github/workflows/canary-release.yml` | Inputs: `project-type`; Secrets: —. | Creates canary builds for Python, npm, or Docker projects; supports custom working directories and build backends (`working-directory`, `build-backend`, `image`, `NPM_TOKEN`). |
| Conventions: Conventional Commits | `.github/workflows/conventional-commits.yml` | Inputs: —; Secrets: —. | Enforces the Conventional Commits spec across PRs. |
| Examples Smoke | `.github/workflows/examples-smoke.yml` | Inputs: —; Secrets: —. | Validates that the example projects in this repository continue to build and test successfully. |
| Permissions Hardened Template | `.github/workflows/permissions-template.yml` | Inputs: —; Secrets: —. | Opinionated starter that applies least-privilege permissions, concurrency, and cache patterns. |
| Test Python Test Matrix | `.github/workflows/test-python-test-matrix.yml` | Inputs: —; Secrets: —. | Regression workflow demonstrating expected behavior for the reusable Python test matrix. |

### Packaging, releases, and distribution

| Workflow | Path | Requirements | Summary |
| --- | --- | --- | --- |
| Artifact Management | `.github/workflows/artifact-management.yml` | Inputs: —; Secrets: `GH_TOKEN`. | Cleans up build artifacts, packages, and container images with retention, size, and registry filters. |
| Changelog Auto PR | `.github/workflows/changelog-auto-pr.yml` | Inputs: —; Secrets: —. | Opens automated PRs with changelog updates using configurable commit messages and branches. |
| Docker Build & Push | `.github/workflows/docker-build-push.yml` | Inputs: `image`; Secrets: —. | Builds and pushes multi-platform container images with optional registry credentials and AWS ECR role assumption. |
| Publish Docker on Tag | `.github/workflows/publish-docker-on-tag.yml` | Inputs: —; Secrets: —. | Builds and publishes Docker images on tag events with optional registry credentials and build args. |
| Release Container | `.github/workflows/release-container.yml` | Inputs: —; Secrets: —. | Publishes versioned container images on semantic tags with provenance attestation. |
| Release Drafter | `.github/workflows/release-drafter.yml` | Inputs: —; Secrets: —. | Generates draft release notes using configurable categories and templates. |
| Semantic Release | `.github/workflows/release.yml` | Inputs: —; Secrets: —. | Automates semantic-release for Node.js projects with configurable Node runtime. |
| Publish to npm (simple) | `.github/workflows/publish-to-npm.yml` | Inputs: —; Secrets: —. | Publishes npm packages from a single job with configurable Node version. |
| Publish to npm (advanced) | `.github/workflows/npm-publish.yml` | Inputs: —; Secrets: `NPM_TOKEN`. | Handles advanced npm publication scenarios including subdirectories and dist-tags. |
| Publish to PyPI (simple) | `.github/workflows/publish-to-pypi.yml` | Inputs: `python-version`, `pip-version`; Secrets: —. | Publishes Python packages with API tokens, configurable Python versions, and governed pip upgrades. |
| Publish to PyPI (trusted publishing) | `.github/workflows/pypi-publish.yml` | Inputs: `python-version`, `build-backend`, `environment`, `pre-release`, `pip-version`; Secrets: —. | Uses OIDC trusted publishing with optional pre-release tagging, build backend selection, environment protection, and pip upgrade policy alignment. |
| Vercel Next.js Deploy | `.github/workflows/vercel-nextjs.yml` | Inputs: `vercel-org-id`, `vercel-project-id`; Secrets: `vercel-token`. | Builds and deploys Next.js apps to Vercel with optional preview/production selection and custom Node versions. |

### Infrastructure, data, and operations

| Workflow | Path | Requirements | Summary |
| --- | --- | --- | --- |
| AWS Lambda Deploy | `.github/workflows/aws-lambda-deploy.yml` | Inputs: `aws-role`, `functions`, `pip-version`; Secrets: —. | Deploys serverless functions via OIDC role assumption with region overrides, structured function definitions, and configurable pip bootstrapping for Python runtimes. |
| Database Migration | `.github/workflows/database-migration.yml` | Inputs: `tool`, `migration-dir`, `environments`, `pip-version`; Secrets: —. | Runs Flyway, Liquibase, or Alembic migrations across multiple environments with optional dry-run mode, Flyway license support, and governed pip upgrades for Alembic. |
| Helm Chart Lint & Test | `.github/workflows/helm-chart-lint-test.yml` | Inputs: —; Secrets: —. | Lints and optionally tests Helm charts, including OCI registry publishing when requested. |
| Infra Lint | `.github/workflows/infra-lint.yml` | Inputs: —; Secrets: —. | Lints Terraform, CloudFormation, and related IaC code with optional path targeting. |
| Kubernetes Manifests Lint | `.github/workflows/k8s-manifests-lint.yml` | Inputs: —; Secrets: —. | Validates Kubernetes manifests with kubeval, kube-score, and policy checks with configurable paths. |
| Multi-Cloud Deploy | `.github/workflows/multi-cloud-deploy.yml` | Inputs: `tool`, `environment`; Secrets: —. | Orchestrates Terraform, Pulumi, or Bicep deployments across AWS, Azure, and GCP with OIDC and backend configuration options (`aws-role-arn`, `azure-*`, `gcp-*`, `env-file`, `backend-config`, `pulumi-backend`, `azure-credentials`). |
| Terraform Apply (AWS OIDC) | `.github/workflows/terraform-aws.yml` | Inputs: `aws-role`; Secrets: —. | Plans and applies Terraform using GitHub OIDC with toggles for region, version, apply mode, and failure rollback. |
| Terraform Plan (PR comment) | `.github/workflows/terraform-plan-comment.yml` | Inputs: —; Secrets: —. | Generates Terraform plans and posts summaries back to pull requests with optional working directory selection. |

### Security and compliance

| Workflow | Path | Requirements | Summary |
| --- | --- | --- | --- |
| CodeQL Analysis | `.github/workflows/codeql-analysis.yml` | Inputs: —; Secrets: —. | Runs CodeQL analysis for Python, JavaScript, and Go with upload permissions preconfigured. |
| Conventional Commits | `.github/workflows/conventional-commits.yml` | Inputs: —; Secrets: —. | Checks commit messages for the Conventional Commits specification. |
| Dependency Review | `.github/workflows/dependency-review.yml` | Inputs: —; Secrets: —. | Annotates pull requests with dependency vulnerability information using GitHub's dependency-review action. |
| Lockfile Consistency | `.github/workflows/lockfile-consistency.yml` | Inputs: `pip-version`; Secrets: —. | Validates that npm, Yarn, pip, and Poetry lockfiles match their manifests with configurable pip bootstrapping. |
| PR Policy | `.github/workflows/pr-policy.yml` | Inputs: —; Secrets: —. | Applies repository policy checks such as title formatting and draft status enforcement. |
| Security Scan | `.github/workflows/security-scan.yml` | Inputs: `paths`, `skip-trivy`, `pip-version`, `skip-npm-signatures`, `skip-java-verify`, `skip-go-verify`; Secrets: —. | Runs Trivy, pip-audit, Bandit, and dependency checks with configurable pip bootstrapping plus optional path targeting and Trivy skip flag. |

## Repository automation workflows

These workflows run locally in this repository to keep the collection healthy and demonstrate expected behavior.

| Workflow | Path | Triggers | Purpose |
| --- | --- | --- | --- |
| Examples Smoke | `.github/workflows/examples-smoke.yml` | `push`, `pull_request` | Builds and tests each project under `examples/` to ensure the samples stay runnable. |
| Python Type Check | `.github/workflows/python-type-check.yml` | `push`, `pull_request`, `workflow_dispatch` | Runs mypy across repository scripts to guard helper utilities. |
| R Package Check | `.github/workflows/r-cmd-check.yml` | `push`, `pull_request`, `workflow_dispatch` | Executes `R CMD check` across supported operating systems for the R examples. |
| R Lint | `.github/workflows/r-lint.yml` | `push`, `pull_request`, `workflow_dispatch` | Lints R sources and examples using the composite R lint action. |
| R Tests (testthat) | `.github/workflows/r-testthat.yml` | `push`, `pull_request`, `workflow_dispatch` | Runs `testthat` suites for the R example projects. |
| Test Python Test Matrix Workflow | `.github/workflows/test-python-test-matrix.yml` | `workflow_dispatch`, `push` | Verifies the reusable Python matrix workflow against known scenarios. |

---

## 📚 Catalogue (detailed index)

### Actions

| Name | Type | Path | Inputs | Outputs | Example |
| --- | --- | --- | --- | --- | --- |
| Python Lint & Type Check | composite | `.github/actions/python-lint` | `python-version`, `enable-mypy`, `pip-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/python-lint@main` |
| Python Type Check (mypy) | composite | `.github/actions/python-type-check` | `python-version`, `working-directory`, `requirements-file`, `extra-dependencies`, `mypy-args`, `pip-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/python-type-check@main` |
| Check Imports vs pyproject | composite | `.github/actions/check-imports` | `paths`, `fail-on`, `format`, `update-pyproject`, `create-pr`, `pr-branch`, `python-version`, `pip-version`, `smart-update` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/check-imports@main` |
| Smart Dependency Update | composite | `.github/actions/smart-dependency-update` | `manifests`, `apply`, `batch-size`, `dependabot`, `repo`, `github-token`, `pip-version` | `report` | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/smart-dependency-update@main` |
| APM Integration | composite | `.github/actions/apm-integration` | `provider`, `api-key`, `app-id`, `environment`, `deployment-id`, `metrics-file` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/apm-integration@main` |
| AWS Lambda Build (Python) | composite | `.github/actions/aws-lambda-build` | `src`, `output-zip`, `python-version`, `pip-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/aws-lambda-build@main` |
| Setup Poetry (with cache) | composite | `.github/actions/setup-poetry` | `python-version`, `install-deps`, `pip-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/setup-poetry@main` |
| Setup R Environment | composite | `.github/actions/setup-r` | `r-version`, `cran-mirror`, `use-public-rspm`, `packages`, `working-directory` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/setup-r@main` |
| R Lint | composite | `.github/actions/r-lint` | `r-version`, `cran-mirror`, `use-public-rspm`, `targets`, `config-file`, `additional-packages`, `working-directory` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/r-lint@main` |
| R Testthat | composite | `.github/actions/r-testthat` | `r-version`, `test-directory`, `install-dependencies`, `use-devtools`, `additional-packages`, `working-directory` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/r-testthat@main` |
| Setup Yarn (Corepack) with cache | composite | `.github/actions/setup-yarn` | `node-version`, `working-directory` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/setup-yarn@main` |
| Secret Scan | composite | `.github/actions/secret-scan` | `args` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/secret-scan@main` |
| Benchmark Smoke | composite | `.github/actions/benchmark-smoke` | `python-version`, `working-directory`, `pytest-args`, `pip-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/benchmark-smoke@main` |
| PR Template Enforcer | composite | `.github/actions/pr-template-enforcer` | – | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/actions/pr-template-enforcer@main` |

### Workflows

| Name | Type | Path | Inputs | Outputs | Example |
| --- | --- | --- | --- | --- | --- |
| CI Monorepo by Path | reusable | `.github/workflows/ci-monorepo-matrix.yml` | `groups` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/ci-monorepo-matrix.yml@main` |
| Infra Lint | reusable | `.github/workflows/infra-lint.yml` | `paths` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/infra-lint.yml@main` |
| Kubernetes Manifests Lint | reusable | `.github/workflows/k8s-manifests-lint.yml` | `paths` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/k8s-manifests-lint.yml@main` |
| Helm Chart Lint & Test | reusable | `.github/workflows/helm-chart-lint-test.yml` | `chart-path`, `publish`, `oci-registry` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/helm-chart-lint-test.yml@main` |
| Publish to npm (simple) | reusable | `.github/workflows/publish-to-npm.yml` | `node-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/publish-to-npm.yml@main` |
| Python Test Matrix | reusable | `.github/workflows/python-test-matrix.yml` | `python-versions`, `os-matrix`, `test-command`, `pip-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/python-test-matrix.yml@main` |
| Python Type Check | reusable | `.github/workflows/python-type-check.yml` | – | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/python-type-check.yml@main` |
| R Lint | reusable | `.github/workflows/r-lint.yml` | – | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/r-lint.yml@main` |
| R Tests (testthat) | reusable | `.github/workflows/r-testthat.yml` | – | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/r-testthat.yml@main` |
| R Package Check | reusable | `.github/workflows/r-cmd-check.yml` | – | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/r-cmd-check.yml@main` |
| Terraform Plan (PR comment) | reusable | `.github/workflows/terraform-plan-comment.yml` | `working-directory` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/terraform-plan-comment.yml@main` |
| Terraform Apply (AWS OIDC) | reusable | `.github/workflows/terraform-aws.yml` | `aws-role`, `aws-region`, `terraform-version`, `working-directory`, `apply`, `destroy-on-failure` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/terraform-aws.yml@main` |
| Multi-Cloud Deploy | reusable | `.github/workflows/multi-cloud-deploy.yml` | `tool`, `environment`, provider creds | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/multi-cloud-deploy.yml@main` |
| AWS Lambda Deploy | reusable | `.github/workflows/aws-lambda-deploy.yml` | `aws-role`, `aws-region`, `functions`, `pip-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/aws-lambda-deploy.yml@main` |
| API Testing | reusable | `.github/workflows/api-testing.yml` | `openapi-spec`, `contract-path`, `base-url`, `contract-type`, `load-script`, `run-zap` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/api-testing.yml@main` |
| Artifact Management | reusable | `.github/workflows/artifact-management.yml` | `retention-days`, `keep-latest`, `max-size-mb`, `package-name`, `registry` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/artifact-management.yml@main` |
| Database Migration | reusable | `.github/workflows/database-migration.yml` | `tool`, `migration-dir`, `environments`, `dry-run`, `pip-version` | `flyway-license-key` | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/database-migration.yml@main` |
| Conventional Commits | reusable | `.github/workflows/conventional-commits.yml` | – | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/conventional-commits.yml@main` |
| Publish to npm (advanced) | reusable | `.github/workflows/npm-publish.yml` | `node-version`, `working-directory`, `tag` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/npm-publish.yml@main` |
| Publish to PyPI (simple) | reusable | `.github/workflows/publish-to-pypi.yml` | `python-version`, `pip-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/publish-to-pypi.yml@main` |
| Release Container | reusable | `.github/workflows/release-container.yml` | – | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/release-container.yml@main` |
| Python Tests & Coverage | reusable | `.github/workflows/coverage-report.yml` | `python-version`, `test-command`, `pip-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/coverage-report.yml@main` |
| PR Policy | reusable | `.github/workflows/pr-policy.yml` | – | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/pr-policy.yml@main` |
| Publish to PyPI (trusted publishing) | reusable | `.github/workflows/pypi-publish.yml` | `python-version`, `build-backend`, `environment`, `pre-release`, `pip-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/pypi-publish.yml@main` |
| Semantic Release | reusable | `.github/workflows/release.yml` | `node-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/release.yml@main` |
| Docker Build & Push | reusable | `.github/workflows/docker-build-push.yml` | `image`, `context`, `dockerfile`, `platforms`, `tags`, `aws-role`, `aws-region` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/docker-build-push.yml@main` |
| Publish Docker (Reusable + Tag Trigger) | reusable | `.github/workflows/publish-docker-on-tag.yml` | `image`, `context`, `dockerfile`, `platforms`, `build-args`, `target`, `labels`, `registry` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/publish-docker-on-tag.yml@main` |
| Python Lint | reusable | `.github/workflows/python-lint.yml` | `python-version`, `enable-mypy`, `pip-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/python-lint.yml@main` |
| Security Scan | reusable | `.github/workflows/security-scan.yml` | `paths`, `skip-trivy`, `pip-version`, `skip-npm-signatures`, `skip-java-verify`, `skip-go-verify` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/security-scan.yml@main` |
| CodeQL Analysis | reusable | `.github/workflows/codeql-analysis.yml` | – | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/codeql-analysis.yml@main` |
| Dependency Review | reusable | `.github/workflows/dependency-review.yml` | – | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/dependency-review.yml@main` |
| Lockfile Consistency | reusable | `.github/workflows/lockfile-consistency.yml` | `pip-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/lockfile-consistency.yml@main` |
| Canary Release | reusable | `.github/workflows/canary-release.yml` | `project-type`, `working-directory`, `build-backend`, `image` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/canary-release.yml@main` |
| Java CI | reusable | `.github/workflows/java-ci.yml` | `build-tool` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/java-ci.yml@main` |
| Deno CI | reusable | `.github/workflows/deno-ci.yml` | `deno-version`, `os-matrix`, `run-tests`, `deploy`, `project` | `deno-deploy-token` | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/deno-ci.yml@main` |
| Node CI | reusable | `.github/workflows/node-ci.yml` | `node-version`, `os-matrix` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/node-ci.yml@main` |
| Rust CI | reusable | `.github/workflows/rust-ci.yml` | – | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/rust-ci.yml@main` |
| Go CI | reusable | `.github/workflows/go-ci.yml` | `go-version` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/go-ci.yml@main` |
| PyTorch Train & Deploy | reusable | `.github/workflows/pytorch-train-deploy.yml` | `python-version`, `train-script`, `benchmark-script`, `model-artifact`, `deploy`, `mlflow-uri` | `hf-token` | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/pytorch-train-deploy.yml@main` |
| Ruby CI | reusable | `.github/workflows/ruby-ci.yml` | `ruby-versions`, `test-command`, `run-tests` | `rubygems-token` | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/ruby-ci.yml@main` |
| Vercel Next.js Deploy | reusable | `.github/workflows/vercel-nextjs.yml` | `vercel-org-id`, `vercel-project-id`, `node-version`, `working-directory`, `prod` | `vercel-token` | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/vercel-nextjs.yml@main` |
| Changelog Auto PR | reusable | `.github/workflows/changelog-auto-pr.yml` | `commit-message`, `branch` | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/changelog-auto-pr.yml@main` |
| Release Drafter | reusable | `.github/workflows/release-drafter.yml` | – | – | `uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/release-drafter.yml@main` |

## Composite Actions in detail

### Setup R Environment

Install a requested R toolchain, configure a CRAN mirror or Posit Public Package Manager, and optionally pre-install packages so subsequent jobs can reuse the library cache.

**Inputs**
* `r-version` (default `release`)
* `cran-mirror` (default `https://cloud.r-project.org`)
* `use-public-rspm` (default `true`)
* `packages` (comma-separated list of CRAN packages, default empty)
* `working-directory` (default `.`)

**Example**

```yaml
steps:
  - name: Prepare R runtime
    uses: DiogoRibeiro7/gh-actions-collection/.github/actions/setup-r@main
    with:
      r-version: '4.3'
      packages: 'tidyverse,lintr'
```

### R Lint (composite)

Provision R with `lintr`, optionally install additional dependencies, and lint selected files or directories using `lintr::lint` and `lintr::lint_dir` depending on the target type.

**Inputs**
* `r-version` (default `release`)
* `targets` (default `R`)
* `config-file` (default empty)
* `additional-packages` (comma-separated list)
* `working-directory` (default `.`)

**Example**

```yaml
steps:
  - name: Lint R sources
    uses: DiogoRibeiro7/gh-actions-collection/.github/actions/r-lint@main
    with:
      targets: 'R,tests/testthat'
      config-file: '.lintr'
```

### R Testthat (composite)

Install dependencies via `remotes`, optionally leverage `devtools`, and execute the project tests with rich summaries suitable for CI logs.

**Inputs**
* `r-version` (default `release`)
* `test-directory` (default `tests/testthat`)
* `install-dependencies` (default `true`)
* `use-devtools` (default `true`)
* `additional-packages` (comma-separated list)
* `working-directory` (default `.`)

**Example**

```yaml
steps:
  - name: Run unit tests
    uses: DiogoRibeiro7/gh-actions-collection/.github/actions/r-testthat@main
    with:
      test-directory: 'tests'
      use-devtools: true
```

## Reusable Workflows

### CI Monorepo by Path

Dispatch workflows only for changed top-level folders.

**Inputs**
* `groups`: JSON mapping of folder to workflow path.

**Example**

```yaml
jobs:
  ci:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/ci-monorepo-matrix.yml@main
    with:
      groups: '{"pkg": ".github/workflows/python-lint.yml"}'
```

### Infra Lint

Run Terraform and CloudFormation linters with optional security scanners (Checkov, tfsec, KICS).

**Inputs**
* `paths` (default `.`)

**Example**

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/infra-lint.yml@main
```

### Kubernetes Manifests Lint

Validate Kubernetes YAML with kubeconform.

**Inputs**
* `paths` (default `.`)

**Example**

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/k8s-manifests-lint.yml@main
```

### Helm Chart Lint & Test

Run `helm lint` and `helm template --dry-run` with optional publishing to GitHub Pages or an OCI registry.

**Inputs**
* `chart-path` (default `.`)
* `publish` (default `false`)
* `oci-registry` (default `''`)

**Example**

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/helm-chart-lint-test.yml@main
    with:
      chart-path: chart
```

### Publish to npm (simple)

Install dependencies, run tests, and publish to npm with provenance.

**Inputs**
* `node-version` (default `20`)

**Example**

```yaml
jobs:
  publish:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/publish-to-npm.yml@main
    secrets:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Python Test Matrix

Run tests across multiple Python versions and operating systems.

**Inputs**
* `python-versions` (JSON array)
* `os-matrix` (JSON array)
* `test-command`
* `pip-version` (default `24.3.1`, set to `latest` for the newest pip)

**Example**

```yaml
jobs:
  test:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/python-test-matrix.yml@main
```

### Python Type Check

Run `mypy` against a project using the Python type-check composite action with sensible defaults.

**Example**

```yaml
jobs:
  type-check:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/python-type-check.yml@main
```

### R Lint

Trigger `lintr` against R scripts, R Markdown files, and package sources. The workflow reuses the `r-lint` composite action and watches for changes to `.lintr` configuration files.

**Example**

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/r-lint.yml@main
```

### R Tests (testthat)

Install dependencies (including optional `devtools`) and execute `testthat` suites, automatically detecting package structures versus standalone test directories.

**Example**

```yaml
jobs:
  tests:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/r-testthat.yml@main
```

### R Package Check

Provision R, install `remotes` and `rcmdcheck`, restore package dependencies, and run `R CMD check --no-manual` for package validation.

**Example**

```yaml
jobs:
  check:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/r-cmd-check.yml@main
```

### Terraform Plan (PR comment)

Generate a Terraform plan and comment on pull requests.

**Inputs**
* `working-directory` (default `.`)

**Example**

```yaml
jobs:
  plan:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/terraform-plan-comment.yml@main
```

### Terraform Apply (AWS OIDC)

Run Terraform plan and apply using AWS credentials from GitHub's OIDC provider with optional automatic rollback.

**Inputs**
* `aws-role` (required)
* `aws-region` (default `us-east-1`)
* `terraform-version` (default `1.8.5`)
* `working-directory` (default `.`)
* `apply` (default `false`)
* `destroy-on-failure` (default `false`)

**Example**

```yaml
jobs:
  apply:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/terraform-aws.yml@main
    with:
      aws-role: arn:aws:iam::123456789012:role/GitHubActionsRole
      apply: true
```

### AWS Lambda Deploy

Deploy zip or container-based Lambda functions across multiple runtimes with optional layers, environment variables, and alias management.

**Inputs**
* `aws-role` (required)
* `aws-region` (default `us-east-1`)
* `functions` (JSON array, required)

**Example**

```yaml
jobs:
  deploy:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/aws-lambda-deploy.yml@main
    with:
      aws-role: arn:aws:iam::123456789012:role/GitHubActions
      functions: '[{"name":"py-fn","runtime":"python3.12","path":"lambda/python"}]'
```

### API Testing

Validate OpenAPI specs, run contract tests with Postman or Pact, perform k6 load testing, and optionally scan with OWASP ZAP.

**Inputs**

* `openapi-spec` (required)
* `contract-path` (required)
* `base-url` (required)
* `contract-type` (default `postman`)
* `load-script` (optional)
* `run-zap` (default `false`)

**Example**

```yaml
jobs:
  api-tests:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/api-testing.yml@main
    with:
      openapi-spec: openapi.yaml
      contract-path: postman-collection.json
      base-url: https://example.com
      load-script: k6-script.js
      run-zap: true
```

### Database Migration

Run database schema migrations for PostgreSQL, MySQL, or SQL Server using Flyway, Liquibase, or Alembic with automatic rollback and migration history tracking.

**Inputs**

* `tool` (required)
* `migration-dir` (required)
* `environments` (required JSON array)
* `dry-run` (default `false`)

**Example**

```yaml
jobs:
  migrate:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/database-migration.yml@main
    with:
      tool: flyway
      migration-dir: db/migrations
      environments: '["dev"]'
    secrets:
      DEV_DATABASE_URL: ${{ secrets.DEV_DATABASE_URL }}
      DEV_DB_USER: ${{ secrets.DEV_DB_USER }}
      DEV_DB_PASSWORD: ${{ secrets.DEV_DB_PASSWORD }}
```

### Conventional Commits

Check that commit messages follow Conventional Commits.

**Example**

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/conventional-commits.yml@main
```

### Publish to npm (advanced)

Build and publish an npm package using yarn or npm.

**Inputs**
* `node-version` (default `20`)
* `working-directory` (default `.`)
* `tag` (default `latest`)

**Example**

```yaml
jobs:
  publish:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/npm-publish.yml@main
    with:
      working-directory: .
      tag: next
    secrets:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Publish to PyPI (simple)

Build a package and publish to PyPI.

**Inputs**
* `python-version` (default `3.12`)

**Example**

```yaml
jobs:
  publish:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/publish-to-pypi.yml@main
```

Use `python scripts/pypi_trusted_publishing_wizard.py` for an interactive setup
that generates this workflow and provides PyPI configuration steps. A VS Code
snippet (`pypi-publish`) is also available for quick insertion. See
[PyPI Trusted Publishing Setup Guide](docs/pypi-trusted-publishing.md) for
troubleshooting tips.

### Workflow Generator

Generate starter workflows for Python or Node projects with pinned actions.

```bash
python scripts/workflow_generator.py python
```

Override the branch or output file if required:

```bash
python scripts/workflow_generator.py node --branch develop --output .github/workflows/ci.yml
```

### Starter Workflow Migrator

Convert GitHub's starter workflows to reuse this collection's hardened
workflows:

```bash
python scripts/migrate_starter_workflows.py .github/workflows/python-package.yml --output .github/workflows/ci.yml
```

See the [migration guide](docs/migrating-from-starter-workflows.md) for
comparisons and gradual rollout strategies.

### Release Container

Publish a container image on tag or manual trigger.

**Example**

```yaml
jobs:
  publish:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/release-container.yml@main
```

### Canary Release

Publish staged artifacts from the `develop` branch or `*-rc` tags.

**Inputs**
* `project-type` (`python`, `npm`, or `docker`)
* `working-directory` (default `.`)
* `build-backend` (Python only; default `poetry`)
* `image` (Docker image name)

**Example**

```yaml
jobs:
  canary:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/canary-release.yml@main
    with:
      project-type: python
      build-backend: poetry
```

### Python Tests & Coverage

Run tests and upload a coverage report.

**Inputs**
* `python-version` (default `3.12`)
* `test-command`

**Example**

```yaml
jobs:
  test:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/coverage-report.yml@main
```

### PR Policy

Label pull requests by size and path.

Path rules live in `.github/labeler.yml`.

**Example**

```yaml
jobs:
  policy:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/pr-policy.yml@main
```

### Publish to PyPI (trusted publishing)

Build and publish to PyPI with optional Poetry backend.

**Inputs**
* `python-version` (default `3.12`)
* `build-backend` (default `build`)
* `environment` (default `pypi`)
* `pre-release` (default `false`)

**Example**

```yaml
jobs:
  publish:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/pypi-publish.yml@main
```

For a full example see [`examples/python-package/.github/workflows/release-pypi.yml`](examples/python-package/.github/workflows/release-pypi.yml).

### Semantic Release

Run semantic-release to publish releases and changelogs.

**Inputs**
* `node-version` (default `20`)

**Example**

```yaml
jobs:
  release:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/release.yml@main
```

### Docker Build & Push

Build and push multi-platform Docker images with optional ECR authentication via OIDC, GitHub Actions cache-based layer caching, and post-build vulnerability scanning. QEMU setup is skipped for single-architecture (`linux/amd64`) builds to reduce overhead.

**Inputs**
* `image`
* `context`
* `dockerfile`
* `platforms`
* `tags`
* `aws-role`
* `aws-region`

**Example**

```yaml
jobs:
  docker:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/docker-build-push.yml@main
    with:
      image: ghcr.io/diogoribeiro7/image
      aws-role: arn:aws:iam::123456789012:role/GitHubActions
```

### Publish Docker on Tag

Build and push a Docker image when tagging or via workflow call.

**Inputs**
* `image`
* `context`
* `dockerfile`
* `platforms`
* `build-args`
* `target`
* `labels`
* `registry`

**Example**

```yaml
jobs:
  docker:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/publish-docker-on-tag.yml@main
```

### Python Lint

Run ruff and optional mypy via the python-lint action.

**Inputs**
* `python-version` (default `3.12`)
* `enable-mypy` (default `false`)

**Example**

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/python-lint.yml@main
```

### Security Scan

Audit dependencies, verify package signatures, and run static analysis with SARIF output.
The workflow caches vulnerability databases, generates SLSA Level 2 attestations for reports, and archives logs for compliance frameworks (e.g., SOC 2, GDPR); see the [Security Scan Compliance Guide](docs/security-scan-compliance.md).

**Inputs**
* `paths` (default `.`)
* `skip-trivy` (default `true`)
* `pip-version` (default `24.3.1`, set to `latest` for the newest pip)
* `skip-npm-signatures` (default `false`)
* `skip-java-verify` (default `false`)
* `skip-go-verify` (default `false`)

**Example**

```yaml
permissions:
  contents: read
  security-events: write
  id-token: write
  attestations: write

jobs:
  scan:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/security-scan.yml@main
    with:
      paths: '.'
      skip-trivy: true
```

### CodeQL Analysis

Run GitHub's CodeQL analysis across Python, JavaScript, and Go.

**Example**

```yaml
jobs:
  analyze:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/codeql-analysis.yml@main
```

### Dependency Review

Check dependency diffs for known vulnerabilities on pull requests.

**Example**

```yaml
jobs:
  review:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/dependency-review.yml@main
```

### Lockfile Consistency

Validate that `poetry.lock` or `yarn.lock` match their manifests.

**Example**

```yaml
jobs:
  lockfile:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/lockfile-consistency.yml@main
```

### Java CI

Install Temurin JDK and run Maven or Gradle tests.

**Inputs**
* `build-tool` (default `maven`)

**Example**

```yaml
jobs:
  test:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/java-ci.yml@main
    with:
      build-tool: maven
```

For a full example see [`examples/java-app/.github/workflows/ci.yml`](examples/java-app/.github/workflows/ci.yml).

### Deno CI

Run `deno lint` and `deno test` across Linux, macOS, and Windows runners. Optionally deploy to [Deno Deploy](https://deno.com/deploy) using `deployctl`.

**Inputs**
* `deno-version` (default `1.x`)
* `os-matrix` (default `["ubuntu-latest","windows-latest","macos-latest"]`)
* `run-tests` (default `true`)
* `deploy` (default `false`)
* `project` (default `''`)

**Example**

```yaml
jobs:
  deno:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/deno-ci.yml@main
    with:
      deploy: false
```

### Node CI

Run Yarn lint and test commands across Linux, macOS, and Windows runners using Corepack.

**Inputs**
* `node-version` (default `20`)
* `os-matrix` (default `["ubuntu-latest","windows-latest","macos-latest"]`)

**Example**

```yaml
jobs:
  build:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/node-ci.yml@main
    with:
      os-matrix: '["ubuntu-latest","windows-latest","macos-latest"]'
```

**Platform notes**
* Steps run in Bash so path separators behave consistently on all platforms.
* Windows runners rely on the Git Bash environment included with the runner image.
* `actions/setup-node` installs Node.js and enables Corepack for Yarn.

### Rust CI

Run `cargo fmt`, `cargo check`, and `cargo clippy`.

**Example**

```yaml
jobs:
  build:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/rust-ci.yml@main
```

See [`examples/rust-crate/.github/workflows/ci.yml`](examples/rust-crate/.github/workflows/ci.yml) for a working sample.

### Go CI

Run `go test` and `golangci-lint`.

**Inputs**
* `go-version` (default `1.22`)

**Example**

```yaml
jobs:
  build:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/go-ci.yml@main
```

The [`examples/go-module/.github/workflows/ci.yml`](examples/go-module/.github/workflows/ci.yml) workflow shows a complete setup.

### Ruby CI

Run tests across multiple Ruby versions with Bundler caching.

**Inputs**
* `ruby-versions` (default `["3.1","3.2"]`)
* `test-command` (default `bundle exec rake test`)
* `run-tests` (default `true`)

**Secrets**
* `rubygems-token` (optional)

**Example**

```yaml
jobs:
  test:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/ruby-ci.yml@main
```

### Vercel Next.js Deploy

Build and deploy a Next.js application to Vercel with retry logic for rate limits.

**Inputs**
* `vercel-org-id`
* `vercel-project-id`
* `node-version` (default `20`)
* `working-directory` (default `.`)
* `prod` (default `true`)

**Secrets**
* `vercel-token`

**Example**

```yaml
jobs:
  deploy:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/vercel-nextjs.yml@main
    with:
      vercel-org-id: ${{ vars.VERCEL_ORG_ID }}
      vercel-project-id: ${{ vars.VERCEL_PROJECT_ID }}
    secrets:
      vercel-token: ${{ secrets.VERCEL_TOKEN }}
```

### Changelog Auto PR

Generate `CHANGELOG.md` and open a pull request with the updates.

**Inputs**
* `commit-message` (default `chore: update changelog`)
* `branch` (default `chore/update-changelog`)

**Example**

```yaml
jobs:
  changelog:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/changelog-auto-pr.yml@main
```

### Release Drafter

Draft release notes based on merged pull requests.

**Example**

```yaml
jobs:
  draft:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/release-drafter.yml@main
```

---

## 📌 Guidelines

* Keep each action self-contained with a clear `README.md`.
* Prefer composite actions unless JavaScript/TypeScript is required.
* Document inputs, outputs, and environment variables.
* Add tests or example workflows where applicable.

---

## 🗺️ Roadmap

The first milestones focus on high‑leverage, broadly reusable workflows and composite actions. Each item links to a suggested path (inputs/outputs, minimal example, and security notes).

### Milestone 1 — Core Quality & Safety

1. **Python Lint & Type Check** (composite)

   * Tools: `ruff`, `flake8` (optional), `pyproject.toml` discovery, `mypy` (optional toggle).
   * Inputs: `paths`, `python-version`, `enable-mypy`.
   * Outputs: annotations.
   * Example reusable workflow: `.github/workflows/python-lint.yml`.
2. **Security Scan** (reusable workflow)

   * Steps: `pip-audit --strict`, `bandit -r`, `trivy fs` (opt-in), SARIF upload.
   * Inputs: `paths`, `skip-trivy`, `pip-version`, `skip-npm-signatures`, `skip-java-verify`, `skip-go-verify`.
3. **Check Imports vs pyproject** (composite)

   * Script to parse imports and compare with `pyproject.toml`.
   * Inputs: `fail-on` (`missing`, `unused`, `both`), `format` (`text`, `json`), `update-pyproject`, `create-pr`, `pip-version` (override the validated pip release or set `latest`).
   * Output: machine-readable JSON artifact or auto-updated `pyproject.toml`.

### Milestone 2 — Build, Test, Cache

4. **Python Test Matrix** (reusable)

   * Matrix over `os: [ubuntu-latest, windows-latest, macos-latest]` and `python: [3.10, 3.11, 3.12]`.
   * Built-in caching for pip/poetry (`actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065` cache, `poetry cache`), `pytest -q` and coverage upload.
5. **Node/TS Lint + Test** (reusable)

   * `corepack enable`, `yarn install --immutable`, `yarn lint`, `yarn test`.
6. **Docker Build & Push** (reusable)

   * Login via OIDC → `docker/build-push-action` with `cache-from/to` and SBOM (`syft`) as artifact.

### Milestone 3 — Release Automation

7. **Semver Tagging & Release Notes** (reusable)

   * Conventional Commits check → `semantic-release` (Node) or `python-semantic-release`.
   * GitHub Release, changelog update, version bump PR.
8. **Publish to PyPI** (reusable)

   * Build with `pipx run build` or `poetry build`; publish via PyPI OIDC token.
   * Inputs: `environment` (protect releases), `pre-release` flag.
9. **Publish to npm** (reusable)

   * `npm publish --provenance`; provenance enabled via OIDC and `id-token: write`.

### Milestone 4 — Cloud & Ops (Optional)

10. **AWS Lambda Build & Package** (composite)

    * Layer or container image build, `docker buildx`, slim wheels, artifact upload.
11. **Infra Lint** (reusable)

    * `cfn-lint`, `tflint`, `checkov` (opt-in), SARIF upload.

### Milestone 5 — Hygiene & Governance

12. **PR Policy** (reusable)

    * Auto‑label, size labels, codeowners check, required status checks, stale bot.
13. **Permissions Hardening** (template)

    * Opinionated defaults: least‑privilege `permissions: read-all`, job‑scoped writes.
14. **Concurrency & Caching Templates**

    * `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }`.
    * Cache keys with `hashFiles()`—document stable vs rolling keys.

---

## 🧩 Reuse Patterns (Examples)

### Call a reusable workflow from another repo

```yaml
jobs:
  security:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/security-scan.yml@main
    with:
      paths: src/**
```

### Use a composite action from this repo

```yaml
steps:
  - uses: actions/checkout@v4
  - name: Lint & Type Check
    uses: DiogoRibeiro7/gh-actions-collection/.github/actions/python-lint@main
    with:
      python-version: '3.12'
      enable-mypy: true
```

---

## 🔐 Security Notes

* Default to `permissions: read-all`; elevate per‑job only when needed (e.g., `id-token: write` for OIDC).
* Pin third‑party actions by commit SHA where feasible.
* Validate all user inputs; avoid shell injection via `shell: bash -euxo pipefail` and quoted vars.

---

## Author

Maintained by [Diogo Ribeiro](https://github.com/DiogoRibeiro7)

Affiliation: ESMAD - Instituto Politécnico do Porto

Contact: <diogo.debastos.ribeiro@gmail.com> / <dfr@esmad.ipp.pt>

ORCID: <https://orcid.org/0009-0001-2022-7072>

## Citation

If you use this repository, please cite it as described in [CITATION.cff](CITATION.cff).

## 📄 License

MIT
