# Multi-Cloud Deploy Workflow

This reusable workflow deploys infrastructure to AWS, Azure, and GCP using Terraform, Pulumi, or Bicep templates.

## Setup
1. Configure OIDC trust relationships for each cloud provider.
2. Create a GitHub environment per deployment target (e.g., `dev`, `prod`).
3. Store any required secrets (such as subscription IDs or service-account emails) in that environment.
4. Optionally create an environment variable file and reference it with the `env-file` input.

## Usage
```yaml
jobs:
  deploy:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/multi-cloud-deploy.yml@develop
    with:
      tool: terraform
      environment: prod
      aws-role-arn: arn:aws:iam::123456789012:role/GithubDeploy
      aws-region: us-east-1
      backend-config: bucket=my-terraform-state,key=prod.tfstate,region=us-east-1
```

## Troubleshooting
- **Authentication errors** – verify OIDC permissions and input IDs.
- **State lock timeouts** – ensure backend supports locking and release stale locks.
- **Quota or region errors** – check provider limits and update the `aws-region` or equivalent inputs.

## Performance Tips
- Use remote state backends close to the target region to keep sync operations under two minutes.
- Run the workflow with the default parallel matrix to deploy to all clouds simultaneously.

## Security Considerations
- Grant the workflow only the minimal cloud IAM permissions required for the deployment.
- Pin the workflow to a specific commit when reusing it.
- Review cost estimates before applying changes to avoid unexpected charges.

## Migration
Existing standalone cloud deployments can migrate by replacing their deployment steps with a call to this workflow and providing equivalent inputs.
