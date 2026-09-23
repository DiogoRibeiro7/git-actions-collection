# Docker app example

This example builds and publishes a container image when a tag is pushed.
It reuses the canonical [`docker-build-push`](../../.github/workflows/docker-build-push.yml) workflow from
this repository.

## Usage

Tag a commit and push it to trigger the release workflow:

```sh
git tag v0.1.0
git push origin v0.1.0
```

The image will be published to `ghcr.io/diogoribeiro7/git-actions-collection` for both `linux/amd64`
and `linux/arm64` platforms.

## Canary Release

Use `.github/workflows/canary.yml` to build an image tagged `:rc` when pushing to `main` or tagging an `*-rc` version.

```yaml
jobs:
  release:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/canary-release.yml@v1
    with:
      project-type: docker
      image: ghcr.io/${{ github.repository }}
```

Examples use the stable `@v1` tag. Pin an exact commit SHA when immutable reproducibility is required.
