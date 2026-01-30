## Testing actions locally

Run the full suite (single command):

```
yarn test
```

Under the hood this runs:

```
pytest -q
bats tests/bash
```

Targeted commands:

```
yarn test:py
yarn test:bash
```

Run a single test file:

```
# Pytest (fake runner harness)
pytest tests/test_fake_runner_composite.py -q

# Bats (bash scripts)
bats tests/bash/actions/test_check_imports.bats
```

Local tooling:

- Python 3.11+ with a venv and `pip install -r requirements-dev.txt`
- bats-core (Linux: `sudo apt-get install bats` or `brew install bats-core`)
- Node 20 with corepack enabled for Yarn (`corepack enable`)
 - Windows: bats is not available by default; install bats or run tests in WSL

Required env vars (set by the harness unless you override):

- `GITHUB_OUTPUT` and `GITHUB_ENV` (used by composite actions to expose outputs)
- `PATH` (fake commands injected for deterministic tests)

Notes on mocks/fakebin:

- Python fake runner tests use PATH shims created by `tests/utils/fakebin.py` to avoid network calls.
- Bash unit tests use `tests/bash/helpers.bash` to inject fake commands and capture output.
- Set `FAKEBIN_FAIL_<tool>=1` to force a stubbed tool to fail (example: `FAKEBIN_FAIL_GIT=1`).
- Use `FAKEBIN_PYTHON_MODE=check-imports` or `FAKEBIN_PYTHON_MODE=smart-update` to drive python stub behavior.
