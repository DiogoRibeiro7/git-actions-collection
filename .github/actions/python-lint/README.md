# Python Lint & Type Check

Run [ruff](https://github.com/astral-sh/ruff) and optionally [mypy](https://mypy-lang.org/) on a project.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `python-version` | no | `3.12` | Python version to use |
| `enable-mypy` | no | `false` | Run mypy type checks |
| `working-directory` | no | `.` | Directory to lint, relative to the workspace |
| `pip-version` | no | `26.2.1` | pip release to install (set to 'latest' to track upstream) |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/python-lint@v1
  with:
    python-version: '3.12'
    enable-mypy: true
```
