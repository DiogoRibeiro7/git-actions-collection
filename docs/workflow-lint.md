# Validate GitHub Actions workflows

Use the [Workflow Lint](../.github/workflows/workflow-lint.yml) reusable workflow to check a repository's `.github/workflows` files. It runs actionlint against workflow syntax and expressions, and ShellCheck against inline shell scripts. Errors fail the pull request check.

```yaml
name: Workflow validation

on:
  pull_request:
    paths:
      - '.github/workflows/**'
      - '.github/actionlint.yaml'

permissions:
  contents: read

jobs:
  workflow-lint:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/workflow-lint.yml@<commit-sha>
```

To lint workflow files outside `.github/workflows`, such as examples or templates, list them as Git pathspecs, one per line. The check fails if they match no tracked file, so a typo cannot silently lint nothing:

```yaml
jobs:
  workflow-lint:
    permissions:
      contents: read
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/workflow-lint.yml@<commit-sha>
    with:
      extra-workflow-files: |
        examples/**/.github/workflows/*.yml
```

Pin the calling job to a reviewed commit SHA while this workflow is in the reference tier. The check scans **all** workflows in the caller repository, including unchanged files. If existing warnings need a documented exception, put a narrow rule in the caller's `.github/actionlint.yaml`; actionlint reads it from the caller's checkout.

This check validates workflow definitions. It cannot prove that external actions, secrets, environments, or deployment credentials will work at runtime.
