# Deno CI and Deploy

This guide explains how to test and deploy Deno applications using the reusable workflow provided by this collection.

## Features

- Runs `deno lint` and `deno test`
- Cross-platform support for Linux, macOS, and Windows
- Caches dependencies for faster builds
- Optional deployment to Deno Deploy with `deployctl`

## Usage

```yaml
jobs:
  deno:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/deno-ci.yml@develop
    with:
      deno-version: '1.x'
```

## Deployment

Enable deployment by setting `deploy: true` and providing the project name and token:

```yaml
jobs:
  deno:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/deno-ci.yml@develop
    with:
      deploy: true
      project: my-app
    secrets:
      deno-deploy-token: ${{ secrets.DENO_DEPLOY_TOKEN }}
```

## Feedback

Have suggestions? Open an issue to help improve Deno support.
