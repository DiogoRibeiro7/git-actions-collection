# Artifact Management Example

Demonstrates the reusable workflow that prunes old build artifacts and container images.

## Setup
1. Store a token with `actions:write` and `packages:delete` scopes as `GH_TOKEN` secret.
2. Adjust retention settings in [cleanup.yml](.github/workflows/cleanup.yml).

## Usage
The workflow runs daily via cron and can be invoked manually:

```bash
gh workflow run cleanup.yml
```

Artifacts for open pull requests and releases are preserved automatically.
