# Setup R Environment

Install R and, optionally, a list of CRAN packages. Use it before steps that run R themselves.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `r-version` | no | `release` | R version to install |
| `cran-mirror` | no | `https://cloud.r-project.org` | CRAN mirror to use for package installation |
| `use-public-rspm` | no | `true` | Leverage the public RStudio Package Manager binary repositories |
| `packages` | no | `""` | Comma-separated list of packages to install |
| `working-directory` | no | `.` | Directory for package installation commands |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/setup-r@v1
  with:
    r-version: '4.4'
    packages: data.table, jsonlite
- run: Rscript analysis.R
```
