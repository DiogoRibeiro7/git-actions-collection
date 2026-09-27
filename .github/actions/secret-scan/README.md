# Secret Scan

Scan the repository for leaked credentials using [gitleaks](https://github.com/gitleaks/gitleaks).
Fails the job if any secrets are detected.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `args` | no | `--no-git -v` | Arguments passed to `gitleaks detect`, separated by spaces or newlines; `--redact` is always added first |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: DiogoRibeiro7/git-actions-collection/.github/actions/secret-scan@v1
```

Scan one folder with a configuration file and keep a JSON report:

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/secret-scan@v1
  with:
    args: |
      --no-git
      --source src
      --config .gitleaks.toml
      --report-format json
      --report-path gitleaks-report.json
```

## How it scans

The action downloads gitleaks 8.30.1 from its GitHub release, checks the archive
against the published SHA-256, and runs `gitleaks detect --redact <args>`. The
default arguments, `--no-git -v`, scan the files in the workspace as they are
checked out rather than the Git history. To scan commits instead, leave out
`--no-git`, optionally narrow the range with `--log-opts`, and check out the
history you want to scan (`actions/checkout` fetches a single commit unless you
set `fetch-depth`).

`--redact` comes first, so findings in the log and in any report show `REDACTED`
instead of the secret. Pass your own `--redact=<percent>` to change how much is
hidden. gitleaks exits with 1 when it finds a leak, which fails the step.

The action needs no token, secret, or licence key, and it sends nothing to a
third party. It runs on Linux x64 and arm64 runners.

## Changes from earlier v1 releases

Earlier v1 releases wrapped `gitleaks/gitleaks-action`. That action declares no
inputs, so `args` was ignored. It needs `GITHUB_TOKEN` to scan pull requests,
which this action did not pass, and a `GITLEAKS_LICENSE` for repositories owned
by an organisation. The scan now runs the gitleaks CLI directly, so `args`
takes effect. Because the default `--no-git` scans every checked-out file, not
only the commits of a pull request, the first run may report secrets that were
already in the repository.
