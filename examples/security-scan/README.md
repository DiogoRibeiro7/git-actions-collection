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
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/security-scan.yml@main
    with:
      paths: '.'
      skip-trivy: true
      skip-npm-signatures: false
      skip-java-verify: false
      skip-go-verify: false
```