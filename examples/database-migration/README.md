# Database Migration Example

Demonstrates using the reusable **Database Migration** workflow with a Flyway SQL script.

## Setup

Create secrets `DEV_DATABASE_URL`, `DEV_DB_USER`, and `DEV_DB_PASSWORD` pointing to a PostgreSQL, MySQL, or SQL Server database.

## Workflow

See [.github/workflows/migrate.yml](.github/workflows/migrate.yml) for invoking the workflow.

## Migrations

This example includes a single Flyway SQL migration located at `migrations/V1__init.sql`.
