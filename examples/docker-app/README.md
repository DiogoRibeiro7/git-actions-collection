# Docker app example

This example builds and publishes a container image when a tag is pushed.
It reuses the [`publish-docker-on-tag`](../../.github/workflows/publish-docker-on-tag.yml) workflow from
this repository.

## Usage

Tag a commit and push it to trigger the release workflow:

```sh
git tag v0.1.0
git push origin v0.1.0
```

The image will be published to `ghcr.io/diogoribeiro7/gh-actions-collection` for both `linux/amd64`
and `linux/arm64` platforms.

## Canary Release

Use `.github/workflows/canary.yml` to build an image tagged `:rc` when pushing to `develop` or tagging an `*-rc` version.

```yaml
jobs:
  release:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/canary-release.yml@main
    with:
      project-type: docker
      image: ghcr.io/${{ github.repository }}
```
