# Cross-repository merge dependencies

Use the cross-repository workflows when a pull request in one repository must
wait for one or more pull requests in other repositories.

The gate publishes a commit status named `cross-repo-merge-gate` by default.
Make that status required in the dependent repository's branch protection rule
or repository ruleset. A pull request then remains blocked until every declared
prerequisite pull request has been merged.

## Dependent repository

Create a small caller workflow in the repository that must wait:

```yaml
name: Cross-repository merge gate

on:
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_dispatch:
    inputs:
      head-sha:
        description: Pull-request head SHA to re-check
        required: true
        type: string

jobs:
  gate:
    permissions:
      statuses: write
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/cross-repo-merge-gate.yml@v1
    with:
      dependencies: >-
        [
          {"repository":"DiogoRibeiro7/project-a","pull_request":42},
          {"repository":"DiogoRibeiro7/project-b","pull_request":17}
        ]
      head-sha: ${{ inputs.head-sha || github.event.pull_request.head.sha }}
    secrets:
      dependency-token: ${{ secrets.CROSS_REPO_READ_TOKEN }}
```

For public prerequisite repositories, omit `dependency-token`. For private
repositories, use a fine-grained token or GitHub App token with read access to
the prerequisite pull requests.

The `workflow_dispatch` trigger is important. It lets an upstream repository
request a fresh evaluation after one of its prerequisite pull requests merges.
The dispatched run writes the result to the dependent pull request's head SHA,
not to the dependent repository's default branch.

## Prerequisite repository

In each repository whose merge can unblock another repository, add a caller that
runs when a pull request closes:

```yaml
name: Notify cross-repository dependents

on:
  pull_request:
    types: [closed]

jobs:
  notify:
    permissions: {}
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/notify-cross-repo-dependents.yml@v1
    with:
      targets: >-
        [
          {
            "repository":"DiogoRibeiro7/dependent-project",
            "pull_request":120,
            "workflow":"cross-repo-gate.yml"
          }
        ]
    secrets:
      dispatch-token: ${{ secrets.CROSS_REPO_DISPATCH_TOKEN }}
```

The reusable notifier skips closed target pull requests and dispatches the
target repository's gate workflow for open ones. Its token needs permission to
read the target pull request and dispatch Actions workflows in that repository.

## Required status

After the dependent workflow has run once, configure the dependent repository
so the `cross-repo-merge-gate` commit status is required before merging. You
can use another context name with the reusable gate's `status-context` input,
but the ruleset and workflow must use the same value.

The workflow itself also fails while prerequisites are outstanding. The commit
status is the authoritative cross-run gate: a later upstream merge can replace
the failed status on the same pull-request head commit with `success`.

## Multiple prerequisites

The `dependencies` input is a JSON array, so one pull request can depend on
several repositories at once. Every prerequisite must be merged. A missing or
unreadable prerequisite fails closed rather than allowing the merge.

The notifier also accepts several targets. This is useful when one shared
library merge unblocks pull requests in several downstream repositories.
