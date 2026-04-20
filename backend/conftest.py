import os

import django
import psycopg
import pytest
from django.conf import settings
from django.test.runner import DiscoverRunner
from django.test.utils import setup_test_environment, teardown_test_environment
from psycopg import sql

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.test_settings")
django.setup()


def _drop_postgres_test_database_if_exists() -> None:
    default_database = settings.DATABASES["default"]
    if default_database["ENGINE"] != "django.db.backends.postgresql":
        return

    test_database_name = default_database["TEST"]["NAME"]
    maintenance_database = os.getenv("POSTGRES_MAINTENANCE_DB", "postgres")

    connection = psycopg.connect(
        dbname=maintenance_database,
        user=default_database["USER"],
        password=default_database["PASSWORD"],
        host=default_database["HOST"],
        port=default_database["PORT"],
        autocommit=True,
    )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid()
            """,
            [test_database_name],
        )
        cursor.execute(
            sql.SQL("DROP DATABASE IF EXISTS {}").format(
                sql.Identifier(test_database_name)
            )
        )

    connection.close()


@pytest.fixture(scope="session", autouse=True)
def django_test_environment():
    setup_test_environment()
    test_runner = DiscoverRunner(verbosity=0, interactive=False)
    database_config = None

    try:
        _drop_postgres_test_database_if_exists()
        database_config = test_runner.setup_databases()
        yield
    finally:
        if database_config is not None:
            test_runner.teardown_databases(database_config)
        else:
            _drop_postgres_test_database_if_exists()
        teardown_test_environment()
