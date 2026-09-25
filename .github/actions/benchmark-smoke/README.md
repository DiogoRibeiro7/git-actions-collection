# Benchmark Smoke

Runs [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) and uploads the results as an artifact.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `python-version` | no | `3.11` | Python version to use |
| `working-directory` | no | `.` | Directory with tests |
| `pytest-args` | no | `""` | Extra arguments for pytest |
| `pip-version` | no | `26.2.1` | pip release to install (set to 'latest' to track upstream) |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example
```yaml
steps:
  - uses: actions/checkout@v4
  - uses: DiogoRibeiro7/git-actions-collection/.github/actions/benchmark-smoke@v1
```
