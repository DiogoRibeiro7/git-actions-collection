# Migrating from GitHub Starter Workflows

GitHub's starter workflows are a great way to begin, but this collection offers
hardened, reusable workflows with pinned dependencies and sensible defaults.
This guide shows how to migrate common starter workflows to their equivalents
here and provides an automated helper for converting existing files.

## Automated Conversion

Use `scripts/migrate_starter_workflows.py` to transform a starter workflow into
one that reuses this collection:

```bash
python scripts/migrate_starter_workflows.py .github/workflows/python-package.yml --output .github/workflows/ci.yml
```

The script detects the language, preserves triggers, and writes a workflow that
calls the appropriate reusable workflow. It refuses to overwrite existing files
and prints the result to stdout if `--output` is omitted.

## Side-by-Side Comparison

### Python

**Starter (`python-package.yml`):**

```yaml
name: Python package
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - run: pip install -r requirements.txt
      - run: pytest
```

**Reusable (`python-test-matrix.yml`):**

```yaml
name: Python package
on: [push]
jobs:
  ci:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/python-test-matrix.yml@main
    with:
      python-versions: '["3.x"]'
```

### Node.js

**Starter (`node.js.yml`):**

```yaml
name: Node.js CI
on:
  push:
    branches: [ main ]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test
```

**Reusable (`node-ci.yml`):**

```yaml
name: Node.js CI
on:
  push:
    branches: [ main ]
jobs:
  ci:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/node-ci.yml@main
    with:
      node-version: '20'
```

## Gradual Migration Strategy

1. Commit the generated workflow alongside the existing starter workflow.
2. Run both workflows in parallel to validate behaviour.
3. Once confidence is gained, remove the original starter workflow.

This approach ensures backward compatibility and a safe rollout.

## Testing Converted Workflows

After migration, invoke `actionlint` on the new workflow and ensure your tests
pass:

```bash
actionlint .github/workflows/ci.yml
```

```bash
pytest
```

These steps confirm that the migrated workflow functions correctly.
