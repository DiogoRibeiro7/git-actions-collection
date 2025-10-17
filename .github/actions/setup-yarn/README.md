# Setup Yarn (Corepack) with cache

Enable Corepack and install dependencies with Yarn using a cache.

## Inputs

| Name | Description | Default |
|------|-------------|---------|
| `node-version` | Node version to use | `20` |
| `working-directory` | Project directory | `.` |

## Outputs

None

## Example

```yaml
- uses: DiogoRibeiro7/gh-actions-collection/.github/actions/setup-yarn@main
  with:
    node-version: '20'
    working-directory: frontend
```
