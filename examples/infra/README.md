# Terraform plan example

This example shows how to comment a Terraform plan on pull requests using the
[`terraform-plan-comment`](../../.github/workflows/terraform-plan-comment.yml) reusable workflow.

## Usage

Open a pull request to trigger the workflow. It runs `terraform init` and
`terraform plan`, then posts the plan as a sticky comment on the PR. A failed
plan is posted too, with its error, and then fails the job. Pushes to `main` run
the same plan but do not post a comment.

No cloud credentials are required because the module contains only local values.
