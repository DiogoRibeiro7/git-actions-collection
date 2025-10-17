# PR Template Enforcer

Fails the workflow if a pull request description is empty or missing the required headings.

## Usage

```yaml
- name: Enforce PR template
  uses: DiogoRibeiro7/gh-actions-collection/.github/actions/pr-template-enforcer@main
```

The action checks for the `## Summary` and `## Testing` sections.
