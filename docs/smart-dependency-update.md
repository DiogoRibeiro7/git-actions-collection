# Smart Dependency Update

Automatically update dependencies across multiple ecosystems with conflict detection and Dependabot alert integration.

## Setup

1. Reference the composite action in your workflow.
2. Provide manifest paths (e.g., `package.json pyproject.toml`).
3. Optionally supply a GitHub token with `security_events: read` to pull Dependabot alerts.
4. Override `pip-version` when your Python projects require a different installer—`24.3.1` is the validated default and `latest` follows upstream releases.

## Usage Example

```yaml
name: Dependency Updates
on:
  workflow_dispatch:
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: DiogoRibeiro7/gh-actions-collection/.github/actions/smart-dependency-update@main
        with:
          manifests: "package.json pyproject.toml"
          apply: "true"
          dependabot: "true"
          repo: "owner/repo"
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Troubleshooting

- Ensure manifests exist; missing files are ignored.
- Conflict detection exits with non-zero status; inspect the `report` output.
- Dependabot API errors are logged but do not fail the update.

## Security Considerations

- Pin the action to a commit SHA.
- Use least-privilege tokens and OIDC for private registries.
- Review updates before merging to detect accidental major upgrades.
