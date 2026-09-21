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
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/security-scan.yml@develop
    with:
      paths: '.'
      skip-trivy: true
      skip-npm-signatures: false
      skip-java-verify: false
      skip-go-verify: false
```

Until the first stable release is cut, examples use `@develop`. For production adoption, pin an exact commit SHA.
