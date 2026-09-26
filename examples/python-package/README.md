# Python Package Example

This minimal package demonstrates how to reuse workflows from
[`git-actions-collection`](../../README.md).

## CI via Reusable Workflows

The workflow in `.github/workflows/ci.yml` runs linting and tests using
reusable workflows.

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/python-lint.yml@v1
  test:
    needs: lint
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/coverage-report.yml@v1
```

Examples use the stable `@v1` tag. Pin an exact commit SHA when immutable reproducibility is required.

## Security Scan

The workflow in `.github/workflows/security.yml` runs dependency and static analysis using the reusable security scan workflow.

```yaml
permissions:
  contents: read
  security-events: write
  id-token: write
  attestations: write

jobs:
  scan:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/security-scan.yml@v1
    with:
      paths: '.'
      skip-trivy: true
```

`security-events: write` uploads the SARIF results. `id-token: write` and
`attestations: write` let the workflow attest its security reports with SLSA
provenance. GitHub checks these grants before any job starts, so omitting them
fails the whole run.

## Additional Security Checks

- `.github/workflows/secret-scan.yml` runs a secret scan on pull requests.
- `.github/workflows/codeql.yml` performs CodeQL analysis for Python, JavaScript, and Go.
- `.github/workflows/dependency-review.yml` warns about vulnerable dependency changes.

## Releasing to PyPI

The workflow in `.github/workflows/release-pypi.yml` publishes the package using [trusted publishing](https://docs.pypi.org/trusted-publishers/).
It defaults to TestPyPI to keep releases safe.

```yaml
jobs:
  publish:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/pypi-publish.yml@v1
    with:
      build-backend: poetry
      environment: pypi
      pre-release: true
```

### Setup steps
1. Create the project on [TestPyPI](https://test.pypi.org/) and add a Trusted Publisher for this repository.
2. In GitHub, create an environment named `pypi` and require reviewers if desired.
3. Tag a release:
   ```sh
   git tag v0.1.0
   git push origin v0.1.0
   ```

No secrets are needed; OIDC handles authentication. Flip `pre-release` to `false` to publish to the real PyPI.

## Canary Release

`.github/workflows/canary.yml` publishes development builds to TestPyPI when pushing to `main` or tagging an `*-rc` version. TestPyPI skips a version it already has, so bump the version (for example to a `.devN` release) for each canary you want uploaded.

```yaml
jobs:
  release:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/canary-release.yml@v1
    with:
      project-type: python
      build-backend: poetry
```

## Benchmark

`.github/workflows/benchmark.yml` runs [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) and uploads the results.

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: DiogoRibeiro7/git-actions-collection/.github/actions/benchmark-smoke@v1
```
