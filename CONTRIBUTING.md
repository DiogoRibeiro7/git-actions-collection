# Testing actions and workflows

Use Linux, macOS, or WSL for the full suite. Native Windows pytest runs skip
tests that require POSIX Bash. Shell files use LF line endings via `.gitattributes`.

## Install tools

Use Python 3.10+ and Node.js 26+. Node.js 26 no longer bundles Corepack, so
install it from npm before enabling it.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
npm install --global corepack@0.36.0
corepack enable
yarn install --frozen-lockfile
```

Install Bats and ShellCheck (`sudo apt-get install bats shellcheck` on Ubuntu),
and [actionlint](https://github.com/rhysd/actionlint/blob/main/docs/install.md).
CI uses actionlint **1.7.12**; with Go 1.25 or newer, install it with:

```bash
go install github.com/rhysd/actionlint/cmd/actionlint@v1.7.12
export PATH="$(go env GOPATH)/bin:$PATH"
```

## Run the checks

Run each command from the repository root. `yarn test` runs only Vitest.

```bash
yarn lint:workflows                  # root workflows, expressions, inline shell
python -m pytest -q                  # Python, action harness, YAML contracts
bats --recursive tests/bash          # shell tests, including nested action tests
yarn lint
yarn typecheck
yarn test
```

CI also audits both Yarn lockfiles, the installed Python development dependencies,
Python tool pins embedded in actions/workflows, the Django example, and the
documentation toolchain. To check
the inline pins locally with `pip-audit` installed:

```bash
python scripts/security_requirements.py > /tmp/action-requirements.txt
pip-audit --strict -r /tmp/action-requirements.txt
```

Dependabot checks the root and maintained example dependency manifests weekly.

Every third-party action is pinned to the commit of a release tag. CI checks
this against each action repository's tags (it needs network access, not a
token):

```bash
python scripts/verify_action_pins.py
```

Pytest enforces the repository's 70% Python-script coverage threshold. For a
focused test run, disable coverage so the entire repository threshold does not
apply to one file:

```bash
python -m pytest --no-cov -q tests/test_fake_runner_composite.py
python -m pytest --no-cov -q tests/python/test_python_test_matrix_workflow.py
bats tests/bash/actions/test_gradle_build.bats
```

## Change a supported interface

The inputs, outputs, secrets, and caller permissions of supported workflows and
actions are recorded in `.github/supported-interfaces.json`, and pytest fails
when they drift. Explain a difference, then record a compatible change in the
same pull request:

```bash
python scripts/interface_snapshot.py --check
python scripts/interface_snapshot.py --write
```

Breaking changes follow the deprecation policy in
[SUPPORT.md](SUPPORT.md#compatibility-and-deprecation).

Each composite action's README lists its inputs and outputs in a section
generated from `action.yml`, and pytest fails when the two differ. Edit the
descriptions in `action.yml`, not the README table, then regenerate:

```bash
python scripts/action_docs.py --write
```

## Choose the right test

| Layer | What it proves | Example |
| --- | --- | --- |
| Unit | Script behavior, argument handling, files, errors | `tests/bash/actions.bats` |
| Composite harness | Input mapping, conditions, step outputs, environment files | `tests/test_fake_runner_composite.py` |
| Contract | Public YAML wiring, defaults, permission requirements | `tests/test_action_contracts.py`, `tests/test_reusable_workflow_permissions.py` |
| Static lint | Workflow syntax, expressions, dependencies, inline shell issues | `yarn lint:workflows` |
| GitHub integration | Actual action dependencies and workflow orchestration | `CI Tests` composite smoke job, `test-python-test-matrix.yml` |

Keep substantial logic in scripts/functions. Test success, invalid input,
dependency failure, and relevant side effects. Use temporary consumer directories,
including a path with spaces. Replace tools/API calls at their boundaries and
assert their arguments, outputs, and exit status. Unit tests must not install
packages, contact real APIs, publish, or deploy.

`tests/utils/fakebin.py` creates executable PATH stubs for Python tests.
`tests/bash/helpers.bash` provides `make_fake` and `make_logger` for direct script
tests. The Bats action harness copies `tests/fakebin` into a temporary directory;
never overwrite the tracked stubs. Use the supported failure switches, for example
`FAKEBIN_FAIL_PYTEST=1`, instead.

## Harness boundaries

`run_action` executes Bash steps and a small expression subset. It reports skipped
`uses:` dependencies in `result.skipped_uses`; their effects must be stubbed.
Unsupported expressions and shells fail explicitly. An action containing only
external actions needs a contract test and a real GitHub run.
`result.executed_steps` distinguishes an all-skipped conditional path from
executed shell code.

`result.outputs` contains only outputs declared by `action.yml`.
`result.step_outputs` exposes internal outputs for assertions. Each step gets its
own command files, and `$GITHUB_ENV` values reach subsequent steps. Composite
inputs must be mapped explicitly through `env:`. The harness does not resolve
broken caller-relative script paths for you.

The Bats action harness is a simpler dispatcher for the actions' single-line
shell commands. It does not evaluate YAML conditions or run external actions;
use Python harness tests for those supported wiring checks.

`run_workflow_step` executes one named shell step with explicitly supplied
expression values. It does not evaluate jobs, matrices, permissions, or triggers.
Use assertions on important YAML contracts and small caller workflows to test
those boundaries. Avoid snapshots of entire workflows.

## Call collection actions from reusable workflows

A step-level `uses: ./...` in a reusable workflow resolves inside the caller's
checkout, where this collection's composite actions do not exist. Check out the
collection at the called workflow's own commit and use the action from there:

```yaml
- name: Check out collection actions
  uses: actions/checkout@<pinned-sha>
  with:
    repository: ${{ job.workflow_repository }}
    ref: ${{ job.workflow_sha }}
    path: .git-actions-collection
    persist-credentials: false
- uses: ./.git-actions-collection/.github/actions/python-lint
```

Keep that checkout out of anything the action scans, as `python-lint.yml` does by
checking the caller's code out into `project/`. `tests/test_reusable_local_actions.py`
enforces the pattern, and `.github/actionlint.yaml` lists the workflows that use
`job.workflow_*`, which actionlint does not know yet.

## CI integration coverage

`.github/workflows/ci-tests.yml` runs the local suites plus root workflow linting.
Its composite smoke job checks out the collection in a subdirectory and executes
`smart-dependency-update` against a separate consumer fixture with real setup
actions. It verifies dry-run/apply behavior, the public JSON output, and failure
propagation. It requires no publishing or deployment secrets.

The existing `test-python-test-matrix.yml` workflow calls the reusable workflow
directly with small test fixtures. New reusable workflows should have similarly
focused caller tests. These integration tests run on GitHub for pull requests to
`main` or manual dispatch; local unit success does not establish runtime compatibility.

`act` is optional for local integration debugging. It does not fully reproduce
permissions, OIDC, environments, or concurrency; see its
[limitations](https://nektosact.com/not_supported.html).

Actionlint checks all root workflows, including reference templates. Its only
configuration exception permits the deliberately disabled optional scanners in
`infra-lint.yml`. Example-project workflows also have their existing smoke/lint
workflow. Keep exceptions narrow and documented.

## Build the documentation site

The site at <https://diogoribeiro7.github.io/git-actions-collection/> is built
with MkDocs from `docs/`, the root policy files, and the example and composite
action READMEs. `scripts/docs_site.py` assembles those pages at build time and
rewrites links written for GitHub, so keep writing ordinary relative links.

It also generates the catalogue and a reference page for every supported,
reference and experimental workflow (`scripts/workflow_docs.py`). A page shows
the workflow's usage, inputs, outputs, secrets and required permissions, read
from its YAML. Start each such workflow with a `#` comment describing what it
does; pytest fails without one, and a link to the workflow's `.yml` file opens
its reference page on the site.

```bash
python -m pip install --require-hashes -r requirements-docs.txt
python -m mkdocs serve    # live preview at http://127.0.0.1:8000
python -m mkdocs build    # strict: broken links and anchors fail
```

The `Docs` workflow builds every pull request that touches Markdown or workflow
and action metadata, and deploys `main` to GitHub Pages. To change the toolchain, edit `requirements-docs.in` and
regenerate the hashed lock with the command at the top of that file.
