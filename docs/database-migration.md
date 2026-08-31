# Database Migration Workflow

Run database schema migrations across environments with automatic rollback and history tracking.

## Usage

```yaml
jobs:
  migrate:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/database-migration.yml@develop
    with:
      tool: flyway # or liquibase, alembic
      migration-dir: migrations
      environments: '["dev","staging"]'
      dry-run: false
    secrets:
      DEV_DATABASE_URL: ${{ secrets.DEV_DATABASE_URL }}
      DEV_DB_USER: ${{ secrets.DEV_DB_USER }}
      DEV_DB_PASSWORD: ${{ secrets.DEV_DB_PASSWORD }}
      STAGING_DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
      STAGING_DB_USER: ${{ secrets.STAGING_DB_USER }}
      STAGING_DB_PASSWORD: ${{ secrets.STAGING_DB_PASSWORD }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `tool` | Migration tool (`flyway`, `liquibase`, `alembic`) | – |
| `migration-dir` | Path to migration files | – |
| `environments` | JSON array of environment names (`["dev"]`) | – |
| `dry-run` | Validate migrations without applying them | `false` |
| `pip-version` | pip release to install when using Alembic-based Python migrations | `24.3.1` |

## Secrets

Environment-specific secrets must follow the naming pattern `<ENV>_DATABASE_URL`, `<ENV>_DB_USER`, and `<ENV>_DB_PASSWORD` for each environment listed in `environments`.

Optional secret `flyway-license-key` enables Flyway Pro features such as `undo`.

## Notes

- Dry runs execute `flyway migrate -dryRunOutput`, `liquibase updateSQL`, or `alembic upgrade --sql` without changing the database.
- On migration failure, the workflow attempts an automatic rollback (`flyway undo`, `liquibase rollbackCount 1`, or `alembic downgrade -1`).
- Migration history is printed and uploaded as an artifact for auditing.
- Long-running migrations can increase job duration; consider zero-downtime strategies and maintenance windows for data-heavy changes.
- When `tool` is set to `alembic`, the workflow adheres to the repository pip upgrade policy: the default `24.3.1` installer is validated in CI, and you can override `pip-version` (or set it to `latest`) if your project requires a newer pip release.
