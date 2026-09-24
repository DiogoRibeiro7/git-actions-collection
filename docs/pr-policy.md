# PR policy workflow

`pr-policy.yml` checks pull-request descriptions and labels pull requests by size
and, optionally, by the paths they change.

## Usage

```yaml
name: PR policy

on:
  pull_request:

jobs:
  policy:
    permissions:
      contents: read
      pull-requests: write
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/pr-policy.yml@v1
```

## What it does

- **Description template:** the job fails unless the pull-request description
  contains `## Summary` and `## Testing` sections.
- **Size label:** `codelytv/pr-size-labeler` labels every pull request by the
  size of its diff.
- **Path labels:** when the calling repository has `.github/labeler.yml`,
  `actions/labeler` adds labels for the paths a pull request changes. Without that
  file the step is skipped. The file must use the labeler v5+ format, where each
  label lists match objects:

```yaml
docs:
  - changed-files:
      - any-glob-to-any-file: docs/**
ci:
  - changed-files:
      - any-glob-to-any-file: .github/workflows/**
```

The older format, which mapped a label straight to a list of globs, is rejected.

Pull requests from forks get a read-only token, so the labelling steps cannot
write labels on them.
