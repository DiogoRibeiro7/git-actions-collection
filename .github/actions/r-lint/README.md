# R Lint

Install R and [lintr](https://lintr.r-lib.org/), then lint R sources. The step fails when lintr reports findings.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `r-version` | no | `release` | R version to install |
| `cran-mirror` | no | `https://cloud.r-project.org` | CRAN mirror to use for package installation |
| `use-public-rspm` | no | `true` | Leverage the public RStudio Package Manager binaries |
| `targets` | no | `R` | Comma or newline separated list of files or directories to lint |
| `config-file` | no | `""` | Optional path to a .lintr or lintr config file |
| `additional-packages` | no | `""` | Additional CRAN packages to install before linting |
| `working-directory` | no | `.` | Directory from which to run lintr |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example

Check out the repository before this step.

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/r-lint@v1
  with:
    r-version: release
    targets: |
      R
      tests
    config-file: .lintr
```
