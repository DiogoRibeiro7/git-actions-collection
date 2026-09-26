# AWS Lambda Build (Python)

Package a Python AWS Lambda function with a slim vendor directory.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `src` | no | `lambda/` | Lambda source folder |
| `output-zip` | no | `artifact/lambda.zip` | Path of the zip to create, relative to the workspace or absolute; its directory is created and an existing file is replaced |
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

## How the package is built

The action copies `src` into a `build/` directory in the workspace, leaving out
`__pycache__` directories and `*.pyc` files. If `src` contains a
`requirements.txt`, it installs those packages into `build/` with
`pip install -t`. It then zips the contents of `build/` into `output-zip`, so the
handler module and its dependencies sit at the root of the archive, as Lambda
expects. `rsync` and `zip` must be available; they are on GitHub-hosted Ubuntu
runners.

`output-zip` may point anywhere, for example `dist/function.zip` or an absolute
path. Its directory is created, and an archive already at that path is replaced
rather than extended. Avoid keeping unrelated files in a `build/` directory at
the workspace root, because they would be packaged too.
