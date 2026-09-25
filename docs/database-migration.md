# Database Migration Workflow

Run database schema migrations across environments with automatic rollback and history tracking.

## Usage

```yaml
jobs:
  migrate:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/database-migration.yml@v1
    with:
      tool: flyway # or liquibase, alembic
      migration-dir: migrations
      environments: '["dev","staging"]'
      dry-run: false
    secrets: inherit
```

The workflow reads each environment's secrets by name, so they cannot be declared
as workflow inputs; pass them with `secrets: inherit`. GitHub rejects a call that
passes secrets the workflow does not declare.

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `tool` | Migration tool (`flyway`, `liquibase`, `alembic`) | – |
| `migration-dir` | Path to migration files | – |
| `environments` | JSON array of environment names (`["dev"]`) | – |
| `dry-run` | Preview the migration SQL instead of applying it | `false` |
| `pip-version` | pip release to install when using Alembic-based Python migrations | `26.2.1` |

## Secrets

Environment-specific secrets must follow the naming pattern `<ENV>_DATABASE_URL`, `<ENV>_DB_USER`, and `<ENV>_DB_PASSWORD` for each environment listed in `environments`.

An optional `FLYWAY_LICENSE_KEY` secret enables Flyway Teams features: dry runs and `undo`. The older `flyway-license-key` secret still works but is deprecated, because repository secret names cannot contain hyphens.

## Notes

- Dry runs print the SQL with `liquibase updateSQL` or `alembic upgrade head --sql`, or write it with `flyway migrate -dryRunOutput`, and skip the migration step. Flyway dry runs need a Teams license key; Flyway Community Edition fails the dry run without touching the database.
- On migration failure, the workflow attempts an automatic rollback (`flyway undo`, which needs Flyway Teams, `liquibase rollbackCount 1`, or `alembic downgrade -1`).
- Migration history is printed and uploaded as an artifact for auditing.
- Long-running migrations can increase job duration; consider zero-downtime strategies and maintenance windows for data-heavy changes.
- When `tool` is set to `alembic`, the workflow adheres to the repository pip upgrade policy: the default `26.2.1` installer is validated in CI, and you can override `pip-version` (or set it to `latest`) if your project requires a newer pip release.
