# Python Type Check

Run [mypy](https://mypy-lang.org/) on a project, optionally installing its requirements and extra packages first.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `python-version` | no | `3.11` | Python version to use |
| `working-directory` | no | `.` | Directory to run commands in |
| `requirements-file` | no | `""` | Optional requirements file to install |
| `extra-dependencies` | no | `""` | Space separated list of additional packages to install |
| `mypy-args` | no | `.` | Arguments to pass to mypy |
| `pip-version` | no | `26.2.1` | pip release to install (set to 'latest' to track upstream) |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example

Check out the repository before this step.

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/python-type-check@v1
  with:
    python-version: '3.12'
    requirements-file: requirements.txt
    extra-dependencies: types-requests
    mypy-args: src
```
