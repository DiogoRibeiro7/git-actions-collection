# Testing Plan

This document inventories composite actions and workflows, highlights high‑risk targets, and proposes a unit‑test layout that is deterministic and Linux‑friendly (no network, no real GH API calls).

## Inventory

### Composite actions

| Name | Path | Type | Scripts invoked | Inputs | Outputs |
| --- | --- | --- | --- | --- | --- |
| APM Integration | `.github/actions/apm-integration/action.yml` | composite | bash (`scripts/apm-integration/notify.sh`) | `provider`, `api-key`, `app-id`, `environment`, `deployment-id`, `metrics-file` | - |
| AWS Lambda Build (Python) | `.github/actions/aws-lambda-build/action.yml` | composite | bash (`scripts/aws-lambda-build/build.sh`) | `src`, `output-zip`, `python-version`, `pip-version` | - |
| Benchmark Smoke | `.github/actions/benchmark-smoke/action.yml` | composite | bash (`scripts/benchmark-smoke/install.sh`, `scripts/benchmark-smoke/run.sh`) | `python-version`, `working-directory`, `pytest-args`, `pip-version` | - |
| Check Imports vs pyproject | `.github/actions/check-imports/action.yml` | composite | bash (`scripts/actions/check-imports/check.sh`, `scripts/actions/check-imports/update.sh`) | `paths`, `fail-on`, `format`, `update-pyproject`, `create-pr`, `pr-branch`, `python-version`, `pip-version`, `smart-update` | `missing` (via `$GITHUB_OUTPUT`) |
| Gradle Build | `.github/actions/gradle-build/action.yml` | composite | bash (`scripts/gradle-build/run.sh`) | `java-version`, `tasks`, `gradle-args`, `working-directory` | - |
| Markdown Lint | `.github/actions/markdown-lint/action.yml` | composite | bash (`scripts/markdown-lint/run.sh`) | `paths`, `config-file`, `node-version` | - |
| PR Template Enforcer | `.github/actions/pr-template-enforcer/action.yml` | composite | bash (`scripts/pr-template-enforcer/enforce.sh`) | - | - |
| Python Lint & Type Check | `.github/actions/python-lint/action.yml` | composite | bash (`scripts/python-lint/run.sh`) | `python-version`, `enable-mypy`, `pip-version` | - |
| Python Type Check | `.github/actions/python-type-check/action.yml` | composite | bash (`scripts/python-type-check/run.sh`) | `python-version`, `working-directory`, `requirements-file`, `extra-dependencies`, `mypy-args`, `pip-version` | - |
| R Lint | `.github/actions/r-lint/action.yml` | composite | bash/R (`scripts/r-lint/package-inputs.sh`, `scripts/r-lint/run-lint.sh`, `scripts/r-lint/lint.R`) | `r-version`, `cran-mirror`, `use-public-rspm`, `targets`, `config-file`, `additional-packages`, `working-directory` | `packages` |
| R Testthat | `.github/actions/r-testthat/action.yml` | composite | bash/R (`scripts/r-testthat/package-inputs.sh`, `scripts/r-testthat/run-tests.sh`, `scripts/r-testthat/test.R`) | `r-version`, `cran-mirror`, `use-public-rspm`, `test-directory`, `install-dependencies`, `additional-packages`, `working-directory`, `use-devtools` | `packages` |
| Secret Scan | `.github/actions/secret-scan/action.yml` | composite | (external action only) | `args` | - |
| Setup Poetry (with cache) | `.github/actions/setup-poetry/action.yml` | composite | bash (`scripts/setup-poetry/install.sh`, `scripts/setup-poetry/configure-cache.sh`, `scripts/setup-poetry/install-deps.sh`) | `python-version`, `install-deps`, `pip-version` | - |
| Setup R Environment | `.github/actions/setup-r/action.yml` | composite | bash/R (`scripts/setup-r/install-packages.sh`, `scripts/setup-r/install-packages.R`) | `r-version`, `cran-mirror`, `use-public-rspm`, `packages`, `working-directory` | - |
| Setup Yarn (Corepack) with cache | `.github/actions/setup-yarn/action.yml` | composite | bash (`scripts/setup-yarn/corepack.sh`, `scripts/setup-yarn/install.sh`) | `node-version`, `working-directory` | - |
| Smart Dependency Update | `.github/actions/smart-dependency-update/action.yml` | composite | bash (`scripts/actions/smart-dependency-update/run.sh`) | `manifests`, `apply`, `batch-size`, `dependabot`, `repo`, `github-token`, `pip-version` | `report` |

### Workflows

| Name | Path | Type | Scripts invoked | Inputs | Outputs |
| --- | --- | --- | --- | --- | --- |
| API Testing | `.github/workflows/api-testing.yml` | workflow | bash | - | - |
| Artifact Management | `.github/workflows/artifact-management.yml` | workflow | bash | - | - |
| Auto upgrade pyproject constraints | `.github/workflows/auto-upgrade-pyproject.yml` | workflow | python, bash | - | - |
| AWS Lambda Deploy | `.github/workflows/aws-lambda-deploy.yml` | workflow | bash | - | - |
| Bash Unit Tests | `.github/workflows/bash-unit-tests.yml` | workflow | bash | - | - |
| Canary Release | `.github/workflows/canary-release.yml` | workflow | - | - | - |
| Changelog Auto PR | `.github/workflows/changelog-auto-pr.yml` | workflow | bash | - | - |
| CI Monorepo by Path | `.github/workflows/ci-monorepo-matrix.yml` | workflow | bash, python | - | - |
| CI Monorepo Runner | `.github/workflows/ci-monorepo-runner.yml` | workflow | bash, curl, mvn, cargo, go, terraform, docker | - | - |
| CodeQL Analysis | `.github/workflows/codeql-analysis.yml` | workflow | - | - | - |
| Concurrency and Caching Template | `.github/workflows/concurrency-caching.yml` | workflow | bash | - | - |
| Conventional Commits | `.github/workflows/conventional-commits.yml` | workflow | node | - | - |
| Python Tests & Coverage | `.github/workflows/coverage-report.yml` | workflow | bash | - | - |
| Database Migration | `.github/workflows/database-migration.yml` | workflow | bash | - | - |
| Deno CI | `.github/workflows/deno-ci.yml` | workflow | deno | - | - |
| Dependency Review | `.github/workflows/dependency-review.yml` | workflow | - | - | - |
| Docker Build & Push | `.github/workflows/docker-build-push.yml` | workflow | bash | - | - |
| .NET CI | `.github/workflows/dotnet-ci.yml` | workflow | bash, dotnet | - | - |
| Examples Smoke & Lint | `.github/workflows/examples-smoke.yml` | workflow | bash, curl | - | - |
| Go CI | `.github/workflows/go-ci.yml` | workflow | go | - | - |
| Helm Chart Lint & Test | `.github/workflows/helm-chart-lint-test.yml` | workflow | bash, curl, helm | - | - |
| Infra Lint | `.github/workflows/infra-lint.yml` | workflow | bash, curl, pip | - | - |
| Java CI | `.github/workflows/java-ci.yml` | workflow | mvn, gradle | - | - |
| JS/TS Unit Tests | `.github/workflows/js-unit-tests.yml` | workflow | node | - | - |
| Kubernetes Manifests Lint | `.github/workflows/k8s-manifests-lint.yml` | workflow | curl | - | - |
| Lockfile Consistency | `.github/workflows/lockfile-consistency.yml` | workflow | bash | - | - |
| Multi-Cloud Deploy | `.github/workflows/multi-cloud-deploy.yml` | workflow | bash | - | - |
| Node CI | `.github/workflows/node-ci.yml` | workflow | node | - | - |
| Publish to npm | `.github/workflows/npm-publish.yml` | workflow | node | - | - |
| Permissions Hardened Template | `.github/workflows/permissions-template.yml` | workflow | bash | - | - |
| PR Policy | `.github/workflows/pr-policy.yml` | workflow | - | - | - |
| Publish Docker (Reusable + Tag Trigger) | `.github/workflows/publish-docker-on-tag.yml` | workflow | bash | - | - |
| Publish to npm | `.github/workflows/publish-to-npm.yml` | workflow | node | - | - |
| Publish to PyPI | `.github/workflows/publish-to-pypi.yml` | workflow | bash | - | - |
| Publish to PyPI | `.github/workflows/pypi-publish.yml` | workflow | bash | - | - |
| Python Lint | `.github/workflows/python-lint.yml` | workflow | - | - | - |
| Python Test Matrix | `.github/workflows/python-test-matrix.yml` | reusable | bash | `python-versions`, `os-matrix`, `test-command`, `pip-version` | - |
| Python Type Check | `.github/workflows/python-type-check.yml` | workflow | - | - | - |
| Python Unit Tests | `.github/workflows/python-unit-tests.yml` | workflow | bash, python | - | - |
| PyTorch Train and Deploy | `.github/workflows/pytorch-train-deploy.yml` | workflow | bash | - | - |
| R Package Check | `.github/workflows/r-cmd-check.yml` | workflow | Rscript | - | - |
| R Lint | `.github/workflows/r-lint.yml` | workflow | - | - | - |
| R Tests (testthat) | `.github/workflows/r-testthat.yml` | workflow | - | - | - |
| Release Container | `.github/workflows/release-container.yml` | workflow | - | - | - |
| Release Drafter | `.github/workflows/release-drafter.yml` | workflow | - | - | - |
| Semantic Release | `.github/workflows/release.yml` | workflow | node | - | - |
| Ruby CI | `.github/workflows/ruby-ci.yml` | workflow | bash | - | - |
| Rust CI | `.github/workflows/rust-ci.yml` | workflow | cargo | - | - |
| Security Scan | `.github/workflows/security-scan.yml` | workflow | bash | - | - |
| Terraform Apply (AWS OIDC) | `.github/workflows/terraform-aws.yml` | workflow | bash | - | - |
| Terraform Plan (PR comment) | `.github/workflows/terraform-plan-comment.yml` | workflow | terraform | - | - |
| Test Python Test Matrix Workflow | `.github/workflows/test-python-test-matrix.yml` | workflow | bash | - | - |
| Unit Tests | `.github/workflows/tests.yml` | workflow | node, python | - | - |
| Vercel Next.js Deploy | `.github/workflows/vercel-nextjs.yml` | workflow | bash | - | - |

## Top 5 high‑risk components (unit‑test first)

1) **Check Imports vs pyproject**  
   - Mutates manifest (`pyproject.toml`), optional PR creation, JSON parsing.
2) **Smart Dependency Update**  
   - Parses/updates manifests and emits JSON report; optional Dependabot API integration.
3) **AWS Lambda Build**  
   - Builds artifacts (zip), copies files, installs deps; sensitive to paths/inputs.
4) **APM Integration**  
   - Constructs HTTP payloads and conditionally reads JSON metrics; error handling is critical.
5) **Gradle Build**  
   - Command composition with task/arg parsing; failure propagation important.

## Unit test contracts (targets)

### 1) Check Imports vs pyproject (`scripts/actions/check-imports/*.sh`)
**Accepted inputs:** `paths`, `fail-on`, `format`, `update-pyproject`, `smart-update`, `pip-version`  
**Side effects:**  
- Writes `missing=<space separated>` to `$GITHUB_OUTPUT`.  
- When `update-pyproject=true`, runs updater scripts (no network in tests).  
**Expected outputs:** stdout from script, `missing` output populated.  
**Error cases:** missing/empty `GITHUB_OUTPUT`, invalid inputs, non‑zero from Python script propagates.

### 2) Smart Dependency Update (`scripts/actions/smart-dependency-update/run.sh`)
**Accepted inputs:** `manifests`, `apply`, `batch-size`, `dependabot`, `repo`, `pip-version`  
**Side effects:**  
- Writes `report=<json>` to `$GITHUB_OUTPUT`.  
**Expected outputs:** stdout contains report JSON.  
**Error cases:** missing `manifests`, missing `GITHUB_OUTPUT`, non‑zero script exit.

### 3) AWS Lambda Build (`scripts/aws-lambda-build/build.sh`)
**Accepted inputs:** `src`, `output-zip`, `pip-version`  
**Side effects:**  
- Creates `artifact/` and `build/` directories; writes zip to `output-zip`.  
**Expected outputs:** stdout includes `Created <output-zip>`.  
**Error cases:** empty `src` or `output-zip`, missing `requirements.txt` should be tolerated.

### 4) APM Integration (`scripts/apm-integration/notify.sh`)
**Accepted inputs:** `provider`, `api-key`, `app-id`, `environment`, `deployment-id`, `metrics-file`  
**Side effects:**  
- Calls `curl` with provider‑specific payload; optional `jq` parsing for metrics.  
**Expected outputs:** warning when latency exceeds threshold.  
**Error cases:** invalid provider, missing `api-key`, missing `app-id` for New Relic.

### 5) Gradle Build (`scripts/gradle-build/run.sh`)
**Accepted inputs:** `tasks`, `gradle-args`, `working-directory`  
**Side effects:**  
- Executes `./gradlew <tasks> <args>` in `working-directory`.  
**Expected outputs:** stdout contains gradle invocation (in tests via fake `gradlew`).  
**Error cases:** empty `tasks`, non‑zero `gradlew` should propagate.

## Proposed test layout

```
tests/
  python/            # pytest-based unit tests (fake runner, script validation)
  bash/              # bats tests for bash scripts
  fixtures/          # golden outputs (JSON, YAML, text)
  fakebin/           # command stubs placed first in PATH
```

Notes:
- Unit tests must not perform network calls or real GH API calls.
- Tests should be Linux‑compatible (bash available) and deterministic.
