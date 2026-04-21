import os

import psycopg
from django.conf import settings
from psycopg import sql

TRUE_VALUES = {"1", "true", "yes", "on"}


def env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.lower() in TRUE_VALUES


def drop_postgres_test_database_if_exists() -> None:
    default_database = settings.DATABASES["default"]
    if default_database["ENGINE"] != "django.db.backends.postgresql":
        if not default_database["ENGINE"].endswith("postgresql"):
            return

    test_database_name = default_database["TEST"]["NAME"]
    maintenance_database = default_database["TEST"].get(
        "MAINTENANCE_DB",
        os.getenv("POSTGRES_MAINTENANCE_DB", "postgres"),
    )

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
