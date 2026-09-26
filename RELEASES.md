# Release Policy

This repository is primarily a personal library of reusable GitHub Actions and workflows. It is distributed directly through GitHub repository refs and GitHub Releases. It is not published through GitHub Marketplace or a package registry.

## Branches

- `main` is the only permanent development branch.
- Changes reach `main` through pull requests.
- Feature, fix, and maintenance branches are temporary.
- `@main` is for development and evaluation. Stable consumers should use the moving major tag such as `@v1` or an exact commit SHA.

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
4. Update `pyproject.toml` so its project version matches the stable version to be released, and turn the `Unreleased` section of `CHANGELOG.md` into `## <version> - <YYYY-MM-DD>`.
5. Run **Repository Release** from GitHub Actions on `main`.
6. Supply the semantic version without the `v` prefix, for example `1.0.0`.
7. The workflow runs a release preflight in a read-only job. It requires GitHub's default branch to be `main` and rejects stale `develop` consumer references. For a stable release it also checks the version in `pyproject.toml`, requires a dated `CHANGELOG.md` section for it, and rejects a leftover `Unreleased` section. It checks that `.github/supported-interfaces.json` matches the supported workflows and actions. Finally, it compares those interfaces with the previous release in the same major version (see [Compatibility](#compatibility)).
8. Only after the preflight passes does a second job, the only one that can write, create the annotated exact tag on the commit the preflight checked, publish a GitHub Release with generated notes, and update the moving major tag.

The release workflow does not publish containers, Python packages, npm packages, Marketplace listings, or other registry artifacts for this repository. Publishing workflows in this collection are reusable building blocks for consumer repositories.

## Prereleases

Prereleases may use semantic versions such as `1.0.0-rc.1` and should be marked as prereleases. A prerelease does not update the moving major tag.

## Compatibility

Within a major release series, changes should preserve the documented public inputs, outputs, secrets, and expected behaviour of supported reusable workflows and composite actions. Breaking changes require a new major version.

The release preflight enforces this. It compares the supported interfaces with the snapshot tagged by the previous release in the same major version and fails on every breaking change it finds. When each reported change is an exception that [SUPPORT.md](SUPPORT.md#compatibility-and-deprecation) allows and the changelog records it, run **Repository Release** again with **allow-breaking-changes**. The job log lists each accepted change.
