# PyPI Trusted Publishing Setup Guide

This guide walks through configuring [trusted publishing](https://docs.pypi.org/trusted-publishers/) using the reusable [`publish-to-pypi`](../.github/workflows/publish-to-pypi.yml) workflow.

## Setup wizard

Run the interactive wizard:

```bash
python scripts/pypi_trusted_publishing_wizard.py
```

The wizard will:

1. Verify the GitHub CLI is installed.
2. Generate `.github/workflows/publish-to-pypi.yml` referencing this collection.
3. Remind you to add a trusted publisher entry on PyPI for your project.

## Pip upgrade policy

The `publish-to-pypi` workflow now exposes a `pip-version` input so you can choose the installer that bootstraps your build backend. By default it installs pip `24.3.1`, the latest release validated in this repository. Set `pip-version: latest` (or a specific version) when you need to test newer pip features—each bump should pass `pytest` in this repo before updating the default to keep releases reproducible.

## VS Code snippet

A ready-to-use snippet (`pypi-publish`) lives in `.vscode/pypi-publish.code-snippets` for quick workflow insertion.

## Troubleshooting

- **`gh: command not found`** – install from <https://cli.github.com/> and run `gh auth login`.
- **Workflow does not trigger** – ensure you create a GitHub release; trusted publishing only runs on `release` events.

## Additional resources

- [PyPI trusted publishing documentation](https://docs.pypi.org/trusted-publishers/)
- [Reusable `publish-to-pypi` workflow](../.github/workflows/publish-to-pypi.yml)
