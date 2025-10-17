# AWS Lambda Build (Python)

Package a Python AWS Lambda function with a slim vendor directory.

## Inputs

| Name | Description | Default |
|------|-------------|---------|
| `src` | Lambda source folder | `lambda/` |
| `output-zip` | Path for generated zip file | `artifact/lambda.zip` |
| `python-version` | Python version for build | `3.12` |

## Outputs

None

## Example

```yaml
- uses: DiogoRibeiro7/gh-actions-collection/.github/actions/aws-lambda-build@main
  with:
    src: lambda
    output-zip: artifact/lambda.zip
```
