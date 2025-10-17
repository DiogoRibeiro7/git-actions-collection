# Setup Poetry (with cache)

Install [Poetry](https://python-poetry.org/), configure caches and optionally install dependencies.

## Inputs

| Name | Description | Default |
|------|-------------|---------|
| `python-version` | Python version to use | `3.12` |
| `install-deps` | Run `poetry install` | `true` |

## Outputs

None

## Example

```yaml
- uses: DiogoRibeiro7/gh-actions-collection/.github/actions/setup-poetry@main
  with:
    python-version: '3.12'
    install-deps: true
```
