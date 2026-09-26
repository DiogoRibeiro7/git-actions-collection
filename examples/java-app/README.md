# Java App Example

This sample uses the reusable Java CI workflow to run Maven tests.

```yaml
# .github/workflows/ci.yml
name: ci
on:
  push:
  pull_request:
jobs:
  build:
    permissions:
      contents: read
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/java-ci.yml@v1
    with:
      build-tool: maven
```

Examples use the stable `@v1` tag. Pin an exact commit SHA when immutable reproducibility is required.
