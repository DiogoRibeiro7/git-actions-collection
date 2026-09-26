# Vercel Next.js Deploy Workflow

Deploy a Next.js application to Vercel using the official CLI, retrying failed deploys.

## Usage

```yaml
jobs:
  deploy:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/vercel-nextjs.yml@v1
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
| `node-version` | Node.js version | `24` |
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
* Retries a failed deploy up to three times, waiting 10 and then 20 seconds, and fails with the CLI's exit code if the last attempt fails.
* Minimal `contents: read` permission prevents unnecessary repository access.
* Supports multiple accounts by accepting organization and project IDs as inputs.
