# GitHub starter workflows

`python-package.yml`, `node.js.yml`, `go.yml`, `maven.yml`, `gradle.yml`,
`ruby.yml`, `dotnet.yml`, `rust.yml`, `deno.yml`, and `r.yml` are copied unchanged
from [actions/starter-workflows](https://github.com/actions/starter-workflows/tree/e3c451d60f119b71caebf13c98ac45da6e15b4b7/ci)
at commit `e3c451d60f119b71caebf13c98ac45da6e15b4b7`, under the MIT License of that
repository (Copyright GitHub). They keep the `$default-branch` placeholder that
GitHub replaces when a starter is added through its UI.

The migration tests run the tool on them as users would. Each `<name>.migrated.yml`
is the expected result; `r.yml` has no reusable workflow to migrate to, so the tool
explains that instead.
