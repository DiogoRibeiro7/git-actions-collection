# Setup Yarn (Corepack) with cache

Enable Corepack and install dependencies with Yarn using a cache.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `node-version` | no | `24` | Node version |
| `working-directory` | no | `.` | Project directory |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/setup-yarn@v1
  with:
    node-version: '24'
    working-directory: frontend
```
