# PR Template Enforcer

Fails the workflow if a pull request description is empty or missing the required headings.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

This action has no inputs.

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Usage

```yaml
- name: Enforce PR template
  uses: DiogoRibeiro7/git-actions-collection/.github/actions/pr-template-enforcer@v1
```

The action checks for the `## Summary` and `## Testing` sections.
