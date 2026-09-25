# AWS Lambda Build (Python)

Package a Python AWS Lambda function with a slim vendor directory.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `src` | no | `lambda/` | Lambda source folder |
| `output-zip` | no | `artifact/lambda.zip` | Output zip path |
| `python-version` | no | `3.12` | Python version for build |
| `pip-version` | no | `26.2.1` | pip release to install (set to 'latest' to track upstream) |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/aws-lambda-build@v1
  with:
    src: lambda
    output-zip: artifact/lambda.zip
```
