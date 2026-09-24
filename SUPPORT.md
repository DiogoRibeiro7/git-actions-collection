# Support Policy

The repository contains more automation than the project can responsibly
promise as a stable public API in its first major release. The v1 support
surface is therefore explicit and intentionally smaller than the full
catalogue.

The canonical machine-readable classification is
`.github/support-matrix.yml`. CI verifies that every composite action and
every workflow file is classified exactly once.

## Support levels

### Supported

Supported components are part of the compatibility promise for the current
major release. Within v1, documented inputs, outputs, secrets, and expected
behaviour should remain backward compatible. Changes should include regression
coverage when practical.

All 16 composite actions are currently supported because each has a direct
Bats contract test under `tests/bash/actions/`.

The supported reusable workflows are:

- `python-test-matrix.yml`
- `security-scan.yml`
- `rust-ci.yml`, `rust-quality.yml`, `rust-security.yml`, `rust-coverage.yml`,
  `rust-docs.yml`, `rust-benchmark.yml`, and `rust-release-preflight.yml`

These workflows have direct repository-level contract tests in addition to
example or self-test coverage. `rust-quality.yml` deliberately overlaps the
format and Clippy steps of `rust-ci.yml`: it is a standalone fast gate that
skips the test suite and also lints tests and other targets.

The public interface of every supported component is recorded in
`.github/supported-interfaces.json`; see
[Compatibility and deprecation](#compatibility-and-deprecation).

### Reference

Reference workflows are useful and may be consumed, but they do not yet have
enough direct behavioural coverage for the project to promise v1 compatibility.
They may be promoted to supported after their interfaces and behaviour are
covered by dedicated tests.

This tier currently contains most language CI, governance, linting, and
template workflows.

### Experimental

Experimental workflows perform publishing, deployment, migration, or other
environment-dependent operations where realistic end-to-end validation is
harder. Their interfaces may change before they are promoted to supported.

Consumers should pin these workflows to an exact commit SHA.

### Internal

Internal workflows operate this repository itself. They are not part of the
consumer API and should not be referenced from other repositories.

## Promotion criteria

A reference or experimental workflow can move to supported when it has:

1. a documented public interface;
2. dedicated tests for its inputs, defaults, permissions, and important
   behavioural branches;
3. at least one maintained executable example where appropriate;
4. no known duplicate workflow serving the same purpose without a documented
   reason;
5. third-party actions pinned consistently with the repository security
   policy.

## Compatibility and deprecation

The public interface of a supported component is its inputs (name, type,
whether required, default), outputs, secrets, and the `GITHUB_TOKEN`
permissions a caller must grant. `.github/supported-interfaces.json` records
it, and CI fails when a supported interface no longer matches that record.
`python scripts/interface_snapshot.py --check` explains each difference;
`--write` records it.

Within a major version:

- **Compatible:** adding an optional input, an output, or an optional secret;
  making a required input or secret optional; needing fewer permissions.
- **Breaking, and not allowed:** removing or renaming an input, output, or
  secret; changing an input's type or default; making an input or secret
  required; requiring an additional permission from callers.

Defaults that pin a tool version, such as `pip-version`, may move to a newer
compatible release of that tool. Record these under `### Changed` in
[CHANGELOG.md](CHANGELOG.md).

To retire part of a supported interface:

1. Start its description with `Deprecated:` and name the replacement. The
   snapshot records the deprecation.
2. Keep it working for the rest of the major version, and emit a
   `::warning::` when it is used, where the component can detect that.
3. Record the deprecation under `### Deprecated` in the changelog.
4. Remove it only in the next major version, with migration notes in that
   release.

A security fix may break compatibility within a major version when keeping
the old behaviour would be unsafe. Its release notes must say so explicitly.

## Versioning

The versioning and release process are defined in [RELEASES.md](RELEASES.md).
Supported consumers should normally use the moving major tag `@v1`. Exact
commit SHAs remain the strongest reproducibility option.

Reference and experimental components do not receive the same compatibility
guarantee merely because they are reachable through a `v1` tag.
