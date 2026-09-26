# Monorepo Example

This example runs a check for each top-level folder, and only for the folders a push or pull
request changed.

## Layout

- `pkg-a/` &ndash; tiny Python package.
- `web-app/` &ndash; minimal Node project.
- `infra/` &ndash; small Terraform module.

The top-level workflow calls [ci-monorepo-matrix](../../.github/workflows/ci-monorepo-matrix.yml)
with a mapping of folders to the kind of check the
[runner](../../.github/workflows/ci-monorepo-runner.yml) performs: `pkg-a` runs pytest, `web-app`
runs its npm test script, and `infra` runs `terraform init` and `terraform validate`.

The workflows inside each folder's `.github/workflows/` show the pipeline that folder would use as
a repository of its own. GitHub runs workflows only from the repository root, so the monorepo CI
does not call them.

## Usage

On pushes or pull requests, only the checks for folders with modified files run.
