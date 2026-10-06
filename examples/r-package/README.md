# R package example

This minimal package exercises the reusable `r-cmd-check.yml` workflow.

Its CI delegates package verification to the collection:

```yaml
jobs:
  check:
    permissions:
      contents: read
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/r-cmd-check.yml@v1
```

The workflow installs R, installs the package dependencies from `DESCRIPTION`,
and runs `R CMD check` through `rcmdcheck`. Use the `r-versions` and
`os-matrix` inputs when a package needs compatibility coverage across R
versions or operating systems.

Examples use the stable `@v1` tag. Pin an exact commit SHA when immutable
reproducibility is required.
