# Terraform plan example

This example shows how to comment a Terraform plan on pull requests using the
[`terraform-plan-comment`](../../.github/workflows/terraform-plan-comment.yml) reusable workflow.

## Usage

Open a pull request to trigger the workflow. It runs `terraform init` and
`terraform plan`, then posts the plan as a sticky comment on the PR. Pushes to
`main` run the same plan but do not post a comment.

No cloud credentials are required because the module contains only local values.
