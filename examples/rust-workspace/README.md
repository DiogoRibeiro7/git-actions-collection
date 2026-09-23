# Rust Workspace Example

A Cargo workspace with three crates, used as the executable contract for releasing
selected workspace crates:

| Crate | Publishable | Depends on |
| --- | --- | --- |
| `gac-example-core` | yes | — |
| `gac-example-cli` | yes | `gac-example-core` (path and version) |
| `gac-example-internal` | no (`publish = false`) | `gac-example-core` (path only) |

The release workflows never publish a whole workspace implicitly. Name the crates to
release, listing each dependency before the crates that depend on it:

```yaml
# .github/workflows/release.yml
jobs:
  publish:
    permissions:
      contents: read
      id-token: write
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-publish.yml@v1
    with:
      packages: gac-example-core gac-example-cli
      dry-run: false
      release-environment: release
```

`packages` accepts whitespace- or comma-separated names. Before anything is uploaded,
`rust-release-preflight.yml` checks the selection in a read-only job and rejects:

- names that are not workspace members, or that are listed twice;
- crates that cannot be published to crates.io (`publish = false`, or a `publish` list
  without `crates-io`);
- a selected crate whose normal or build dependency is an unpublishable workspace crate;
- a list that places a crate before one of its selected workspace dependencies.

It then runs one verified `cargo package` for the whole selection, so
`gac-example-cli` is verified against the freshly packaged `gac-example-core` rather
than against crates.io. Selecting several packages requires Cargo 1.90 or newer.

A crate may be released without its workspace dependencies only when the required
versions are already on crates.io; the preflight reports that assumption as a notice.
With `dry-run: true`, the default, only the preflight runs.

Workspace crates can also get their own GitHub Releases, one crate per tag:

```yaml
jobs:
  github-release:
    permissions:
      contents: write
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/rust-github-release.yml@v1
    with:
      package-name: gac-example-core
      tag-prefix: gac-example-core-v
      dry-run: false
```

GitHub Release creation stays separate from crates.io publication, so each can be gated
and retried independently.
