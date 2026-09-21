# Check Imports vs pyproject

Compare imported Python modules against dependencies listed in `pyproject.toml`.

## Inputs

| Name | Description | Default |
|------|-------------|---------|
| `paths` | Space separated paths to scan | `src tests` |
| `fail-on` | `missing`, `unused`, `both`, or `none` | `missing` |
| `format` | Output format: `text` or `json` | `text` |
| `update-pyproject` | Add missing packages to `pyproject.toml` | `false` |
| `create-pr` | Open a PR when updates occur | `false` |
| `pr-branch` | Branch name used when `create-pr` is true | `deps/check-imports` |
| `python-version` | Python version to run the checker | `3.12` |

## Outputs

None

## Example

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/check-imports@develop
  with:
    paths: "src tests"
    update-pyproject: true
    create-pr: true
```
