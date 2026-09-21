# API Testing Example

Demonstrates the API Testing workflow against a simple ping endpoint served by httpbin.

## Setup

No setup required; the workflow hits https://httpbin.org which echoes requests.

## Workflow

```yaml
name: API Tests
on: [push]
jobs:
  api-tests:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/api-testing.yml@develop
    with:
      openapi-spec: openapi.yaml
      contract-path: postman-collection.json
      base-url: https://httpbin.org
      load-script: k6-script.js
      run-zap: false
```

Until the first stable release is cut, examples use `@develop`. For production adoption, pin an exact commit SHA.
