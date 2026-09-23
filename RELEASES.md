# Release Policy

This repository is primarily a personal library of reusable GitHub Actions and workflows. It is distributed directly through GitHub repository refs and GitHub Releases. It is not published through GitHub Marketplace or a package registry.

## Branches

- `main` is the only permanent development branch.
- Changes reach `main` through pull requests.
- Feature, fix, and maintenance branches are temporary.
- `@v1` is for development and evaluation. Stable consumers should use the moving major tag such as `@v1` or an exact commit SHA.

## Stable releases

Stable releases use semantic version tags:

- exact release: `v1.0.0`
- moving major tag: `v1`

The exact tag is immutable. The moving major tag is advanced to the latest compatible release in that major series.

Stable consumers should use one of these forms:

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
7. The workflow runs a release preflight that requires GitHub's default branch to be `main`, rejects stale `develop` consumer references, and validates stable release metadata against `pyproject.toml`.
8. Only after the preflight passes does it create the annotated exact tag, publish a GitHub Release with generated notes, and update the moving major tag.

The release workflow does not publish containers, Python packages, npm packages, Marketplace listings, or other registry artifacts for this repository. Publishing workflows in this collection are reusable building blocks for consumer repositories.

## Prereleases

Prereleases may use semantic versions such as `1.0.0-rc.1` and should be marked as prereleases. A prerelease does not update the moving major tag.

## Compatibility

Within a major release series, changes should preserve the documented public inputs, outputs, secrets, and expected behaviour of supported reusable workflows and composite actions. Breaking changes require a new major version.
