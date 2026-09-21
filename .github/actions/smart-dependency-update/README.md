# Smart Dependency Update Action

Batch-update dependencies across multiple languages with conflict detection and Dependabot alert integration.

## Inputs

| Name | Required | Description |
| --- | --- | --- |
| `manifests` | yes | Space-separated list of manifest files (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Gemfile`) |
| `apply` | no | Apply updates to files when `true` (default `false`) |
| `batch-size` | no | Max packages to update in one run (default `50`) |
| `dependabot` | no | Fetch Dependabot alerts (default `false`) |
| `repo` | no | `owner/repo` for Dependabot API calls |
| `github-token` | no | Token with `security_events: read` for Dependabot API |

## Outputs

| Name | Description |
| --- | --- |
| `report` | JSON summary containing applied updates, detected conflicts, and Dependabot alerts |

## Usage

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/smart-dependency-update@develop
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
