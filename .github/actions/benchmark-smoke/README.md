# Benchmark Smoke

Runs [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) and uploads the results as an artifact.

## Inputs
- `python-version` (default `3.11`)
- `working-directory` (default `.`)
- `pytest-args` – extra arguments passed to `pytest`

## Example
```yaml
steps:
  - uses: actions/checkout@v4
  - uses: DiogoRibeiro7/git-actions-collection/.github/actions/benchmark-smoke@develop
```
