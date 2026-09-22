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
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/java-ci.yml@main
    with:
      build-tool: maven
```

Until the first stable release is cut, examples use `@main`. For production adoption, pin an exact commit SHA.
