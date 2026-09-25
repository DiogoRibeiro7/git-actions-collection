# Security Scan Example

This example shows how to call the reusable security scan workflow.

```yaml
permissions:
  contents: read
  security-events: write
  id-token: write
  attestations: write

jobs:
  scan:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/security-scan.yml@v1
    with:
      paths: '.'
      dependency-install-command: python -m pip install -e .
      bandit-args: '-ll -ii'
      skip-trivy: true
      skip-npm-signatures: false
      skip-java-verify: false
      skip-go-verify: false
```

The optional `dependency-install-command` lets `pip-audit` inspect the dependency closure installed by the consumer project. Without it, `pip-audit` audits the root `requirements.txt`, or else the dependencies your `pyproject.toml` resolves to, and warns when it finds neither. The scanners are installed outside the workspace, so Bandit only scans your code. `bandit-args` controls Bandit's severity/confidence or other CLI flags while preserving `-ll -ii` as the default. Stable consumers may use `@v1`; pin an exact commit SHA when immutable reproducibility is required.
