# Deno Example App

This example demonstrates how to reuse the collection's Deno CI workflow.

## Running Locally

```bash
deno task lint
deno task test
```

## CI/CD

The workflow [`ci.yml`](.github/workflows/ci.yml) invokes the reusable [Deno CI workflow](../../.github/workflows/deno-ci.yml) from this repository.
