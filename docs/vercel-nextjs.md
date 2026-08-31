# Vercel Next.js Deploy Workflow

Deploy a Next.js application to Vercel using the official CLI with retry logic for rate limits.

## Usage

```yaml
jobs:
  deploy:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/vercel-nextjs.yml@develop
    with:
      vercel-org-id: ${{ vars.VERCEL_ORG_ID }}
      vercel-project-id: ${{ vars.VERCEL_PROJECT_ID }}
    secrets:
      vercel-token: ${{ secrets.VERCEL_TOKEN }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `vercel-org-id` | Vercel organization or team ID | – |
| `vercel-project-id` | Vercel project ID | – |
| `node-version` | Node.js version | `20` |
| `working-directory` | Path to Next.js app | `.` |
| `prod` | Deploy to production (`--prod`) | `true` |

## Secrets

| Name | Description |
| --- | --- |
| `vercel-token` | Vercel API token with deploy permissions |

## Outputs

| Name | Description |
| --- | --- |
| `deployment-url` | URL of the deployed application |

## Notes

* Uses the official [Vercel CLI](https://vercel.com/docs/cli) to interact with Vercel's API.
* Retries failed deploys up to three times when rate limits are encountered.
* Minimal `contents: read` permission prevents unnecessary repository access.
* Supports multiple accounts by accepting organization and project IDs as inputs.
