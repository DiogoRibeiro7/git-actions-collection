# API Testing Workflow

Reusable workflow for validating API specifications, contracts, performance, and security.

## Usage

```yaml
name: CI
on: [push]
jobs:
  test:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/api-testing.yml@develop
    with:
      openapi-spec: openapi.yaml
      contract-path: postman-collection.json
      base-url: https://example.com
      load-script: k6-script.js
      run-zap: true
```

## Inputs

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `openapi-spec` | string | yes | Path to OpenAPI/Swagger spec |
| `contract-type` | string | no | `postman` (default) or `pact` |
| `contract-path` | string | yes | Path to contract test file |
| `base-url` | string | yes | API base URL |
| `load-script` | string | no | k6 script for load testing |
| `run-zap` | boolean | no | Run OWASP ZAP API scan |
| `graphql-schema` | string | no | GraphQL schema path |
| `auth-command` | string | no | Shell command for auth token |

## Security Considerations
- Pin all third-party actions to commit SHA
- Use least-privilege secrets and tokens
- Sanitize any auth command output before logging

## Troubleshooting
- Ensure spec files are valid and accessible
- Verify API is reachable at the provided base URL
- ZAP scans may require longer timeouts for large APIs

## Performance Tips
- Provide minimal test data to speed up runs
- Use targeted k6 scripts to limit load scope

## Migration
This workflow replaces ad-hoc API test scripts with a unified, reusable approach.
