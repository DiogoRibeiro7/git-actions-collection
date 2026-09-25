# Secret Scan

Scan the repository for leaked credentials using [gitleaks](https://github.com/gitleaks/gitleaks).
Fails the job if any secrets are detected.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `args` | no | `--no-git -v` | Arguments passed to gitleaks |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example
```yaml
steps:
  - uses: actions/checkout@v4
  - uses: DiogoRibeiro7/git-actions-collection/.github/actions/secret-scan@v1
```
