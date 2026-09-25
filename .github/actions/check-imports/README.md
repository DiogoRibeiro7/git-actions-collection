# Check Imports vs pyproject

Compare imported Python modules against dependencies listed in `pyproject.toml`.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `paths` | no | `src tests` | Paths to scan for Python files |
| `fail-on` | no | `missing` | missing \| unused \| both \| none |
| `format` | no | `text` | Output format: text or json |
| `update-pyproject` | no | `false` | If true, add missing packages to pyproject.toml |
| `create-pr` | no | `false` | Create a pull request with pyproject changes |
| `pr-branch` | no | `deps/check-imports` | Branch name for the PR when create-pr is true |
| `python-version` | no | `3.12` | Python version to run the checker |
| `pip-version` | no | `26.2.1` | pip release to install (set to 'latest' to track upstream) |
| `smart-update` | no | `false` | Use smart dependency updater on pyproject.toml |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/check-imports@v1
  with:
    paths: "src tests"
    update-pyproject: true
    create-pr: true
```
