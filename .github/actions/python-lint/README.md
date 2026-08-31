# Python Lint & Type Check

Run [ruff](https://github.com/astral-sh/ruff) and optionally [mypy](https://mypy-lang.org/) on a project.

## Inputs

| Name | Description | Default |
|------|-------------|---------|
| `python-version` | Python version to use | `3.12` |
| `enable-mypy` | Run mypy type checks | `false` |

## Outputs

None

## Example

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/python-lint@develop
  with:
    python-version: '3.12'
    enable-mypy: true
```
