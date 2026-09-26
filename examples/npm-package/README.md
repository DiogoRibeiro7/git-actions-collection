# npm package example

This sample project shows how to lint, test, and publish a Node package using the reusable workflows from this collection.

## CI

`.github/workflows/ci.yml` installs dependencies with Corepack's Yarn and runs lint and test:

```yaml
jobs:
  lint-test:
    steps:
      - uses: actions/checkout@v4
      - uses: DiogoRibeiro7/git-actions-collection/.github/actions/setup-yarn@v1
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

Use `.github/workflows/canary.yml` to publish pre-release packages under the `next` dist-tag when pushing to `main` or tagging an `*-rc` version. Each run publishes a unique version, `<package.json version>-canary.<run number>.<run attempt>`, because npm refuses to publish the same version twice.

```yaml
jobs:
  release:
    permissions:
      contents: read
      id-token: write
      packages: write
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/canary-release.yml@v1
    with:
      project-type: npm
    secrets:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Examples use the stable `@v1` tag. Pin an exact commit SHA when immutable reproducibility is required.
