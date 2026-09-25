# Markdown Lint

Run [markdownlint-cli](https://github.com/DavidAnson/markdownlint-cli) on Markdown
files with minimal setup.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `paths` | no | `.` | Paths to lint |
| `config-file` | no | `""` | Path to configuration file |
| `node-version` | no | `24` | Node version to use |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Usage

### Basic

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/markdown-lint@v1
```

### Custom configuration and paths

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/markdown-lint@v1
  with:
    paths: |
      README.md
      docs/
    config-file: .markdownlint.yml
    node-version: '24'
```

### Full workflow with caching

<!-- markdownlint-disable MD013 -->
```yaml
name: docs
on:
  pull_request:
    paths: "**/*.md"
jobs:
  lint:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/cache@v4
        with:
          path: ~/.npm
          key:
            ${{ runner.os }}-markdownlint-${{ hashFiles('**/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-markdownlint-
      - uses: DiogoRibeiro7/git-actions-collection/.github/actions/markdown-lint@v1
        with:
          config-file: .markdownlint.yml
          paths: docs/
```
<!-- markdownlint-enable MD013 -->

## Troubleshooting

- **`markdownlint: command not found`** – ensure the `actions/setup-node` step
  succeeded, especially on self-hosted runners.
- **`No files matching`** – verify that `paths` resolves to existing Markdown
  files.
- **`Cannot read configuration file`** – make sure `config-file` is committed and
  the path is correct.

## Performance & Best Practices

- Restrict `paths` and use workflow `paths` filters so the action runs only when
  Markdown files change.
- Cache the npm directory or use a prebuilt container image to avoid
  reinstalling `markdownlint-cli` on every run.
- Maintain a `.markdownlintignore` file to skip generated or vendor directories.

## Security Considerations

- Third-party actions, such as `actions/setup-node`, are pinned by commit SHA to
  mitigate supply-chain attacks.
- Review and update pinned SHAs regularly to receive security patches.
- Run the workflow with read-only permissions (`contents: read`) when linting
  pull requests from forks.
- Treat configuration files from untrusted contributors cautiously; lint rules
  can execute expensive regular expressions.

## Migration Guide

### From `DavidAnson/markdownlint-cli2-action`

```yaml
- uses: DavidAnson/markdownlint-cli2-action@v15
+ uses: DiogoRibeiro7/git-actions-collection/.github/actions/markdown-lint@v1
```

### From `github/super-linter`

Replace the Markdown section of Super Linter with this action for faster,
focused linting:

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/markdown-lint@v1
  with:
    paths: docs/
```

## Configuration Tips

- Provide a custom configuration file with `config-file` when project-specific
  rules are needed.
- Adjust `paths` to lint only certain directories or files.
