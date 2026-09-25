# R Testthat

Install R and run [testthat](https://testthat.r-lib.org/). By default, when the working directory has a `DESCRIPTION` file, the action installs the package's dependencies and runs `devtools::test()`; `install-dependencies` and `use-devtools` turn these off. Otherwise it runs the standalone tests in `test-directory`, and skips when that directory does not exist.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `r-version` | no | `release` | R version to install |
| `cran-mirror` | no | `https://cloud.r-project.org` | CRAN mirror to use for package installation |
| `use-public-rspm` | no | `true` | Leverage the public RStudio Package Manager binaries |
| `test-directory` | no | `tests/testthat` | Directory containing standalone testthat tests |
| `install-dependencies` | no | `true` | Install package dependencies declared in DESCRIPTION |
| `additional-packages` | no | `""` | Additional CRAN packages to install before running tests |
| `working-directory` | no | `.` | Directory from which to execute tests |
| `use-devtools` | no | `true` | Use devtools::test() when a DESCRIPTION file is present |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example

Check out the repository before this step.

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/r-testthat@v1
  with:
    r-version: release
    additional-packages: mockery
```
