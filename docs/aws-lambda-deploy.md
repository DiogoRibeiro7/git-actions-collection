# AWS Lambda Deploy Workflow

Deploy multiple AWS Lambda functions across runtimes with optional layers, environment variables, and alias management.

## Usage

```yaml
jobs:
  deploy:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/aws-lambda-deploy.yml@develop
    with:
      aws-role: arn:aws:iam::123456789012:role/GitHubActions
      aws-region: us-east-1
      functions: |
        [
          {
            "name": "py-fn",
            "runtime": "python3.12",
            "path": "lambda/python",
            "handler": "app.handler",
            "package-type": "zip",
            "env": "{\"LOG_LEVEL\":\"info\"}",
            "layers": "arn:aws:lambda:us-east-1:123456789012:layer:requests:1",
            "alias": "prod"
          },
          {
            "name": "node-fn",
            "runtime": "nodejs20.x",
            "path": "lambda/node",
            "package-type": "zip"
          }
        ]
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `aws-role` | ARN of IAM role assumed via OIDC | – |
| `aws-region` | AWS region for operations | `us-east-1` |
| `functions` | JSON array of function configs | – |
| `pip-version` | pip release installed before building Python packages (`latest` tracks upstream) | `24.3.1` |

Each function object supports:

| Key | Description |
| --- | --- |
| `name` | Lambda function name |
| `runtime` | Runtime (python*, nodejs*, dotnet*, go*, java*, provided*) |
| `path` | Source path relative to repo root |
| `handler` | Handler for zip packages |
| `package-type` | `zip` or `image` |
| `env` | JSON map of environment variables |
| `layers` | Comma-separated layer ARNs |
| `s3-bucket` | S3 bucket for oversized zips |
| `alias` | Alias name to update |
| `subnet-ids` / `security-group-ids` | VPC configuration |

## Secrets

No secrets required; uses AWS OIDC for authentication.

## Notes

* Deploys in parallel using a matrix of functions.
* Skips deployment when source paths have no changes.
* Automatically uploads oversized packages to S3.
* Rolls back function alias on deployment failure.
* Python functions follow the repository’s pip upgrade policy: `24.3.1` is the validated default and you can override `pip-version` (including `latest`) when you need a newer installer.
