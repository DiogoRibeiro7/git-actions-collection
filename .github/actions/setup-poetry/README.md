# Setup Poetry (with cache)

Install [Poetry](https://python-poetry.org/), configure caches and optionally install dependencies.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `python-version` | no | `3.12` | Python version |
| `install-deps` | no | `true` | Run 'poetry install' |
| `pip-version` | no | `26.2.1` | pip release to install (set to 'latest' to track upstream) |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/setup-poetry@v1
  with:
    python-version: '3.12'
    install-deps: true
```
