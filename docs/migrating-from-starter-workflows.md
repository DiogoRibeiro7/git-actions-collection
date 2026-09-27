# Migrating from GitHub Starter Workflows

GitHub's starter workflows are a great way to begin, but this collection offers
hardened, reusable workflows with pinned dependencies and sensible defaults.
This guide shows how to migrate common starter workflows to their equivalents
here and provides an automated helper for converting existing files.

## Automated Conversion

From a checkout of this repository, run the migration tool on a starter workflow:

```bash
python -m scripts.migrate_starter_workflows path/to/python-package.yml --dry-run
python -m scripts.migrate_starter_workflows path/to/python-package.yml --output .github/workflows/ci.yml
```

`--dry-run` explains what the tool found and prints the workflow it would write,
without writing anything. Without `--output`, the workflow goes to stdout. The
tool refuses to overwrite an existing file.

`--json` prints a machine-readable report instead: the detected `ecosystem`, the
`job` it came from, the reusable `workflow` and its `uses:` reference, the
`permissions` and `inputs` of the new job, the `notes` explained below, the
`output` file written (or `null`), and the `migrated` workflow text. Combine it
with `--output` to write the file and report on it in one step.

The tool:

- finds the first job that sets up a known ecosystem and replaces it with a call
  to the matching reusable workflow, declaring the permissions that workflow
  needs;
- resolves `${{ matrix.<name> }}` references, so a version matrix such as
  `python-version: ["3.9", "3.10", "3.11"]` becomes
  `python-versions: '["3.9", "3.10", "3.11"]'`, and keeps the starter's runner
  (`runs-on`) as `os-matrix`;
- keeps a single `pytest` command as `test-command`;
- copies the triggers, replacing the `$default-branch` placeholder of GitHub's
  raw starter templates with `main`, or with `--default-branch <name>`;
- lists every step it did not carry over, such as a separate lint step, so you
  can check that the reusable workflow covers it or add another one;
- flags unquoted versions that YAML turned into numbers, such as `3.10` read as
  `3.1`.

It exits with status 1, and explains why, when it finds no workflow to call.

| Starter sets up | Migrated to |
| --- | --- |
| `actions/setup-python` | `python-test-matrix.yml` |
| `actions/setup-node` with Yarn | `node-ci.yml` |
| `actions/setup-node` with npm or pnpm | nothing yet: `node-ci.yml` runs Yarn only |

## Side-by-Side Comparison

### Python

**Starter (`python-package.yml`, shortened from GitHub's template):**

```yaml
name: Python package
on:
  push:
    branches: [ "$default-branch" ]
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v3
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: python -m pip install flake8 pytest
      - name: Lint with flake8
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
      - name: Test with pytest
        run: pytest
```

**Reusable (`python-test-matrix.yml`):**

```yaml
name: Python package
on:
  push:
    branches: [ main ]
jobs:
  ci:
    permissions:
      contents: read
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/python-test-matrix.yml@v1
    with:
      python-versions: '["3.9", "3.10", "3.11"]'
      os-matrix: '["ubuntu-latest"]'
      test-command: pytest
```

`python-test-matrix.yml` installs the project itself (`pip install .`, or
`requirements.txt` without a `pyproject.toml`) together with pytest. The dry run
notes that the flake8 step was not carried over; add `python-lint.yml` for it.

### Node.js

`node-ci.yml` runs `yarn install --immutable`, `yarn lint`, and `yarn test`, so
only Yarn projects can migrate to it. GitHub's `node.js.yml` starter uses npm; for
npm and pnpm starters the tool explains that no reusable workflow fits yet and
writes nothing.

**Starter (a Yarn project):**

```yaml
name: Node.js CI
on:
  push:
    branches: [ main ]
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18.x, 20.x, 22.x]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: yarn
      - run: yarn install --immutable
      - run: yarn test
```

**Reusable (`node-ci.yml`):**

```yaml
name: Node.js CI
on:
  push:
    branches: [ main ]
jobs:
  ci:
    permissions:
      contents: read
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/node-ci.yml@v1
    with:
      node-version: 22.x
      os-matrix: '["ubuntu-latest"]'
```

`node-ci.yml` tests one Node.js version, so the tool keeps the newest one and
says so. It also runs `yarn lint`, so `package.json` needs a `lint` script.

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
