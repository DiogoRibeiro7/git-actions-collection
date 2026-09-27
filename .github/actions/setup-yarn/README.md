# Setup Yarn (Corepack) with cache

Enable Corepack and install dependencies with Yarn using a cache.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `node-version` | no | `24` | Node version |
| `working-directory` | no | `.` | Directory with package.json and yarn.lock |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/setup-yarn@v1
  with:
    node-version: '24'
    working-directory: frontend
```

## How it works

1. `actions/setup-node` installs `node-version`. Node.js 25 and newer no longer
   bundle Corepack, so on those versions the action installs Corepack 0.36.0
   with npm before running `corepack enable`.
2. Corepack provides the Yarn release named by the `packageManager` field of
   `package.json`, for example `"packageManager": "yarn@4.18.1"`. Pin it there so
   every run uses the same Yarn.
3. If `working-directory` has a `yarn.lock`, the action installs from it without
   changing it: `yarn install --immutable` on Yarn 2 and newer, and
   `yarn install --frozen-lockfile` on Yarn 1, which silently ignores
   `--immutable`. A `package.json` that no longer matches the lockfile fails the
   step. Without a `yarn.lock`, nothing is installed.

## Caching

The cache step saves the project's Yarn state (`.yarn/cache`, `.yarn/patches`,
`.yarn/unplugged`, `.yarn/build-state.yml`, and `.pnp.cjs`), keyed on
`yarn.lock`. Yarn 4 keeps downloaded packages in a global cache by default
(`enableGlobalCache: true`), outside those paths, so they are downloaded again on
each run. Set `enableGlobalCache: false` in `.yarnrc.yml` to keep them in
`.yarn/cache`, where the action caches them. Yarn 1 uses its own global cache,
which this action does not save.
