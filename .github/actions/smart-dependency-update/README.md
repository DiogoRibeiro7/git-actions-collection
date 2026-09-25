# Smart Dependency Update Action

Batch-update dependencies across multiple languages with conflict detection and Dependabot alert integration.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `manifests` | yes |  | Space-separated list of manifest files (package.json, pyproject.toml, Cargo.toml, go.mod, Gemfile) |
| `apply` | no | `false` | If true, apply updates to manifests |
| `batch-size` | no | `50` | Max number of packages to update |
| `dependabot` | no | `false` | Fetch Dependabot alerts |
| `repo` | no |  | owner/repo for Dependabot API |
| `github-token` | no |  | Token that can read Dependabot alerts (security-events: read), used when dependabot is true |
| `pip-version` | no | `26.2.1` | pip release to install (set to 'latest' to track upstream) |

## Outputs

| Output | Description |
| --- | --- |
| `report` | JSON report of updates, detected conflicts and Dependabot alerts |
<!-- END GENERATED REFERENCE -->

## Usage

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/smart-dependency-update@v1
  with:
    manifests: "package.json pyproject.toml"
    apply: "true"
    dependabot: "true"
    repo: "owner/repo"
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Security Considerations

- Pin this action to a commit SHA for production use.
- Provide a short-lived token via OIDC when accessing private package registries.
- Review the generated report before committing updates to ensure no unintended major version bumps.

## Troubleshooting

- Ensure manifest paths exist in the repository.
- Conflicts will cause the action to exit with status `1`; inspect the `report` output for details.
- Dependabot API calls require `security_events: read` permission on the provided token.
