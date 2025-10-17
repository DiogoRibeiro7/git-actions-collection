# Artifact Management Workflow

Reusable workflow that prunes old build artifacts, package versions, and container images using age and size policies while preserving assets for active pull requests and releases.

## Usage

```yaml
name: Cleanup
on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:
jobs:
  cleanup:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/artifact-management.yml@main
    secrets:
      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    with:
      retention-days: 30
      keep-latest: 5
      package-name: ghcr.io/owner/app
```

## Inputs

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `retention-days` | number | no | Delete artifacts older than this many days (default `30`) |
| `keep-latest` | number | no | Number of most recent artifacts to always keep (default `5`) |
| `max-size-mb` | number | no | Delete artifacts larger than this size in MB (default `500`) |
| `package-name` | string | no | GitHub Packages name for pruning old versions |
| `registry` | string | no | Package type for cleanup (default `container`) |

## Security Considerations
- The workflow requires a token with `actions` and `packages` deletion rights; prefer short-lived fine‑grained tokens.
- Review artifacts before deletion to avoid removing data needed for audits or external systems.

## Troubleshooting
- Ensure `GH_TOKEN` has permission to delete artifacts and packages.
- Artifacts tied to open pull requests or releases are skipped; close or draft PRs to trigger removal.
- Deleting package versions may require elevated scopes for private registries.

## Performance Tips
- Schedule daily runs during off-peak hours to minimize impact.
- Adjust `keep-latest` and `retention-days` to balance storage use and recovery needs.

## Migration
This workflow replaces manual artifact cleanup scripts by automating retention policies across builds and packages.
