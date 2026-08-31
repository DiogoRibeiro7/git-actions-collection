# GitHub Actions Collection

A tested collection of reusable GitHub Actions, workflows, and CI/CD utilities for software and data projects.

The repository centralises automation that would otherwise be copied between projects: language-specific CI, packaging and release workflows, security checks, dependency governance, infrastructure automation, and small composite actions for recurring setup and quality gates.

## Status

> **Pre-v1 public toolkit.** This repository does not yet publish a stable GitHub release channel.

- `develop` is the current integration branch.
- `main` is the intended stable branch, but it is not yet the canonical consumer surface.
- For experimentation, consumers may reference `@develop`.
- For production use before the first stable release, pin an exact commit SHA rather than a moving branch.
- The v1 hardening work will define the supported surface, synchronise `main`, and publish versioned release tags.

## What is in the repository

| Area | Purpose |
| --- | --- |
| `.github/actions/` | Composite actions for recurring setup, linting, testing, dependency checks, and build tasks. |
| `.github/workflows/` | Reusable workflows and repository automation for CI, releases, security, infrastructure, and publishing. |
| `scripts/` | Python and shell utilities used by actions and maintenance workflows. |
| `tests/` | Pytest, Vitest, and Bats coverage for utilities, action contracts, and workflow behaviour. |
| `examples/` | Small example projects showing how the reusable automation is consumed. |
| `docs/` | Extended guides for workflows that need more context than a YAML file can provide. |

## High-value building blocks

The collection covers a broad set of stacks, but the most useful pieces are the reusable engineering controls rather than the basic language templates.

### Dependency and repository governance

- **Check Imports vs pyproject** compares Python imports with declared dependencies and can optionally update project metadata.
- **Smart Dependency Update** inspects `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, and `Gemfile`, detects cross-manifest conflicts, and emits a structured update report.
- **Conventional Commits**, **PR policy**, **dependency review**, and **lockfile consistency** workflows provide repository-level quality gates.

### Security and supply chain

- Secret scanning with gitleaks.
- CodeQL analysis for supported languages.
- Dependency review for vulnerable changes.
- Container build and release workflows with provenance support.
- Least-privilege workflow templates and OIDC-oriented deployment examples.

### Python and R engineering

- Python linting and type checking with Ruff and mypy.
- Python test matrices across configurable Python and operating-system versions.
- Poetry setup with caching.
- R setup, linting, and `testthat` helpers.
- Trusted PyPI publishing workflow.

### Delivery and infrastructure

- Docker build and publication workflows.
- AWS Lambda packaging and deployment helpers.
- Terraform and multi-cloud deployment examples.
- Artifact retention and cleanup automation.
- Canary and semantic-release workflows.

## Using a reusable workflow

During the pre-v1 period, `develop` is suitable for evaluation:

```yaml
name: Python CI

on:
  pull_request:
  push:

jobs:
  tests:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/python-test-matrix.yml@develop
    with:
      python-versions: '["3.11", "3.12"]'
```

For production use before the first stable release, replace `@develop` with the exact commit SHA you have validated.

## Using a composite action

```yaml
steps:
  - uses: actions/checkout@v4
  - name: Check Python imports
    uses: DiogoRibeiro7/git-actions-collection/.github/actions/check-imports@develop
```

The same pinning rule applies: use a commit SHA when reproducibility matters.

## Selected reusable workflows

| Workflow | Purpose |
| --- | --- |
| `python-test-matrix.yml` | Configurable Python test matrix across Python and OS versions. |
| `security-scan.yml` | Dependency and static-analysis security checks with SARIF/artifact output. |
| `pypi-publish.yml` | PyPI publication using trusted publishing/OIDC. |
| `docker-build-push.yml` | Multi-platform container builds and registry publication. |
| `terraform-aws.yml` | Terraform validation, planning, and AWS-oriented deployment flow. |
| `api-testing.yml` | OpenAPI/contract validation with optional load and security checks. |
| `ci-monorepo-matrix.yml` | Path-aware CI orchestration for monorepos. |
| `pytorch-train-deploy.yml` | Example ML training, artifact, benchmark, and deployment pipeline. |

See `.github/workflows/` for the complete catalogue and `docs/` for detailed guides.

## Selected composite actions

| Action | Purpose |
| --- | --- |
| `check-imports` | Compare imports with Python dependency declarations. |
| `smart-dependency-update` | Analyse and optionally update dependencies across several manifest formats. |
| `python-lint` | Run Ruff and optional mypy checks. |
| `python-type-check` | Configurable mypy execution for a repository or subdirectory. |
| `setup-poetry` | Install Python/Poetry and configure dependency caching. |
| `r-lint` | Provision R and run `lintr`. |
| `r-testthat` | Provision R dependencies and run `testthat`. |
| `secret-scan` | Run gitleaks against repository content. |
| `aws-lambda-build` | Build a Python Lambda deployment archive. |
| `benchmark-smoke` | Run pytest-benchmark smoke checks and retain the output. |

## Local development

Python 3.10+ and Node.js are required for the repository test harness. Bats is required for the shell-action tests.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
corepack enable
yarn install --immutable
```

Run the main checks with:

```bash
yarn lint
yarn typecheck
yarn test
pytest -q
bats tests/bash
```

## Testing approach

Reusable automation is executable code, so the repository does not treat YAML as documentation-only content.

The test suite includes:

- unit tests for Python maintenance utilities;
- Bats tests for shell-backed composite actions;
- TypeScript/Vitest tests for JavaScript helpers;
- a local fake-runner harness for composite action behaviour;
- smoke workflows for the example projects;
- repository-contract tests for public references and generated artefacts.

## Security model

Reusable workflows should request only the permissions they need. Consumers remain responsible for reviewing permissions, secrets, environments, cloud roles, and third-party actions before adoption.

Where a workflow performs a privileged operation, prefer:

1. short-lived OIDC credentials over long-lived cloud secrets;
2. explicit `permissions` blocks;
3. immutable third-party action pins where practical;
4. protected environments for publication and deployment;
5. exact repository commit or release pins for reusable workflows.

## Road to v1

The first stable release will be cut only after the repository has a smaller, explicit support contract. The current hardening sequence is:

1. clean repository identity and generated artefacts;
2. make `main` the canonical stable branch;
3. classify workflows and actions as supported, reference, or experimental;
4. remove or consolidate duplicate workflow variants;
5. audit third-party action pins and permissions;
6. ensure every advertised supported example is exercised in CI;
7. publish the first versioned GitHub release and stable major tag.

That sequence deliberately favours a smaller reliable surface over a larger catalogue of unchecked snippets.

## Contributing

See `CONTRIBUTING.md` for development and testing guidance. Changes to reusable actions or workflows should include a regression test or executable example when practical.

## Licence

MIT. See `LICENSE`.
