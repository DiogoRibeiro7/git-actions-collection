# Django Web App Example

This project shows a tiny [Django](https://www.djangoproject.com/) web app.
It demonstrates PostgreSQL integration and how to reuse workflows from
[`gh-actions-collection`](../../README.md).

## Local development

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Or run everything in containers:

```bash
docker-compose up
```

## CI/CD via reusable workflows

The workflow in `.github/workflows/ci.yml` runs linting, tests on a Python matrix,
and builds a container image using reusable workflows.

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/python-lint.yml@main
  test:
    needs: lint
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/python-test-matrix.yml@main
    with:
      test-command: python manage.py test
  docker:
    needs: test
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/docker-build-push.yml@main
    with:
      image: ghcr.io/${{ github.repository }}
    secrets: inherit
```

Replace `DiogoRibeiro7` with your own GitHub namespace when adopting.

## Database configuration

`dj-database-url` reads the `DATABASE_URL` environment variable to configure the
connection. If it is undefined, the app uses a local SQLite file. The included
`docker-compose.yml` provisions a PostgreSQL instance for local development.

## Tests

Run unit tests with:

```bash
python manage.py test
```
