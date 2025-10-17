from pathlib import Path


def test_example_sql_contains_create():
    sql = Path('examples/database-migration/migrations/V1__init.sql').read_text()
    assert 'CREATE TABLE' in sql
