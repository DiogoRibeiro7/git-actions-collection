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

## How imports are matched

The action collects the top-level modules that files under `paths` import. It
drops standard-library modules and folders at the workspace root, which it
treats as local packages. It compares what is left with the dependency names in
`pyproject.toml`: `[project].dependencies` and `[tool.poetry.dependencies]`.
Each PEP 508 requirement counts by its name alone, so `packaging>=25.0`,
`requests[socks] >= 2.32` and `numpy<2; python_version < '3.13'` match
`import packaging`, `import requests` and `import numpy`. Names are compared
case-insensitively, with `_` and `-` treated as equal.

The import name must match the distribution name. A module whose distribution
has another name, such as `import yaml` from `PyYAML`, is reported as missing
and its dependency as unused. Scan such code with `fail-on: none`, or keep it
outside `paths`.
