# PR Template Enforcer

Fails the workflow if a pull request description is empty or missing the required headings.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `body` | no | `${{ github.event.pull_request.body }}` | Pull request description to check; defaults to the body of the pull request that triggered the workflow |
| `required-sections` | no | `## Summary ## Testing` | Text the description must contain, one entry per line (usually Markdown headings) |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Usage

```yaml
- name: Enforce PR template
  uses: DiogoRibeiro7/git-actions-collection/.github/actions/pr-template-enforcer@v1
```

By default the action reads the description of the pull request that triggered
the workflow and checks that it contains `## Summary` and `## Testing`. Run it on
`pull_request` or `pull_request_target` events: other events have no pull request
description, so the check fails as if the description were empty.

To require your own template's headings, list them one per line:

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/pr-template-enforcer@v1
  with:
    required-sections: |
      ## What
      ## Why
      ## Rollback plan
```

## How sections are matched

Each entry in `required-sections` must appear somewhere in the description, as
plain text rather than a regular expression. Surrounding spaces are ignored, so
an indented YAML block works. The match is a substring, so `## Summary` is also
found in `### Summary`. The action lists every missing entry before it fails. A
description that is empty or only whitespace fails regardless of the sections.

Pass `body` to check other text, for example a description fetched from the
GitHub API in a `workflow_dispatch` run.
