# Python Package Example

This minimal package demonstrates how to reuse workflows from
[`gh-actions-collection`](../../README.md).

## CI via Reusable Workflows

The workflow in `.github/workflows/ci.yml` runs linting and tests using
reusable workflows.

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/python-lint.yml@main
  test:
    needs: lint
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/coverage-report.yml@main
```

Replace `DiogoRibeiro7` with your GitHub organization or username when adopting.

## Security Scan

The workflow in `.github/workflows/security.yml` runs dependency and static analysis using the reusable security scan workflow.

```yaml
jobs:
  scan:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/security-scan.yml@main
    with:
      paths: '.'
      skip-trivy: true
```

The workflow requires the following permissions to upload SARIF results:

```yaml
permissions:
  contents: read
  security-events: write
```

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
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/pypi-publish.yml@main
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

`.github/workflows/canary.yml` publishes development builds to TestPyPI when pushing to `develop` or tagging an `*-rc` version.

```yaml
jobs:
  release:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/canary-release.yml@main
    with:
      project-type: python
      build-backend: poetry
```

## Benchmark

`.github/workflows/benchmark.yml` runs [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) and uploads the results.

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: DiogoRibeiro7/gh-actions-collection/.github/actions/benchmark-smoke@main
```
