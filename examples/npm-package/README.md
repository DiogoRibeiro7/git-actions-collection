# npm package example

This sample project shows how to lint, test, and publish a Node package using the reusable workflows from this collection.

## CI

`.github/workflows/ci.yml` installs dependencies with Corepack's Yarn and runs lint and test:

```yaml
jobs:
  lint-test:
    steps:
      - uses: actions/checkout@v4
      - uses: DiogoRibeiro7/git-actions-collection/.github/actions/setup-yarn@develop
      - run: yarn lint
      - run: yarn test
```

## Release

Push a tag to trigger the publish workflow:

```sh
git tag v0.1.0
git push origin v0.1.0
```

`.github/workflows/release.yml` calls the reusable npm publish workflow.
Set the `NPM_TOKEN` secret with an npm token that has publish rights.

## Canary Release

Use `.github/workflows/canary.yml` to publish pre-release packages under the `next` dist-tag when pushing to `develop` or tagging an `*-rc` version.

```yaml
jobs:
  release:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/canary-release.yml@develop
    with:
      project-type: npm
    secrets:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Until the first stable release is cut, examples use `@develop`. For production adoption, pin an exact commit SHA.
