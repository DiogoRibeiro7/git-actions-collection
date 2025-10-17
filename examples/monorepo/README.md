# Monorepo Example

This example shows how to fan out work to language-specific workflows only when their paths change.

## Layout

- `pkg-a/` &ndash; tiny Python package.
- `web-app/` &ndash; minimal Node project.
- `infra/` &ndash; small Terraform module.

Each folder exposes a local reusable workflow in `.github/workflows/`.
The top-level workflow calls the [ci-monorepo-matrix](../../.github/workflows/ci-monorepo-matrix.yml) workflow with a mapping of folders to those reusable workflows.

## Usage

On pushes or pull requests, only the workflows for folders with modified files run.
