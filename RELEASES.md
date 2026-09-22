# Release Policy

This repository is primarily a personal library of reusable GitHub Actions and workflows. It is distributed directly through GitHub repository refs and GitHub Releases. It is not published through GitHub Marketplace or a package registry.

## Branches

- `main` is the only permanent development branch.
- Changes reach `main` through pull requests.
- Feature, fix, and maintenance branches are temporary.
- Consumers may use `@main` for evaluation, but production consumers should prefer immutable commit SHAs until a stable release is published.

## Stable releases

Stable releases use semantic version tags:

- exact release: `v1.0.0`
- moving major tag: `v1`

The exact tag is immutable. The moving major tag is advanced to the latest compatible release in that major series.

Once `v1` exists, normal consumers should use one of these forms:

```yaml
uses: DiogoRibeiro7/git-actions-collection/.github/workflows/python-test-matrix.yml@v1
```

or, when maximum reproducibility is required, an exact commit SHA.

## Release procedure

Repository releases are intentionally manual.

1. Merge all intended changes into `main`.
2. Confirm required CI checks are green.
3. Review the public workflows, actions, examples, and documentation.
4. Update `pyproject.toml` so its project version matches the stable version to be released.
5. Run **Repository Release** from GitHub Actions on `main`.
6. Supply the semantic version without the `v` prefix, for example `1.0.0`.
7. The workflow validates the stable release version against `pyproject.toml`, creates the annotated exact tag, publishes a GitHub Release with generated notes, and updates the moving major tag.

The release workflow does not publish containers, Python packages, npm packages, Marketplace listings, or other registry artifacts for this repository. Publishing workflows in this collection are reusable building blocks for consumer repositories.

## Prereleases

Prereleases may use semantic versions such as `1.0.0-rc.1` and should be marked as prereleases. A prerelease does not update the moving major tag.

## Compatibility

Within a major release series, changes should preserve the documented public inputs, outputs, secrets, and expected behaviour of supported reusable workflows and composite actions. Breaking changes require a new major version.
