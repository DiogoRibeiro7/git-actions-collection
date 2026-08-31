# Secret Scan

Scan the repository for leaked credentials using [gitleaks](https://github.com/gitleaks/gitleaks).
Fails the job if any secrets are detected.

## Inputs
- `args` – optional CLI arguments passed to gitleaks (default `--no-git -v`).

## Example
```yaml
steps:
  - uses: actions/checkout@v4
  - uses: DiogoRibeiro7/git-actions-collection/.github/actions/secret-scan@develop
```
