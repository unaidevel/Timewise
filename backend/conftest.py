import os

import django
import pytest
from django.test.runner import DiscoverRunner
from django.test.utils import setup_test_environment, teardown_test_environment

from config.testing import drop_postgres_test_database_if_exists, env_flag

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.test_settings")
django.setup()


@pytest.fixture(scope="session", autouse=True)
def django_test_environment():
    keepdb = env_flag("TESTALL_KEEPDB")
    dropdb = env_flag("TESTALL_DROPDB")

    setup_test_environment()
    test_runner = DiscoverRunner(verbosity=0, interactive=False, keepdb=keepdb)
    database_config = None

    try:
        if dropdb or not keepdb:
            drop_postgres_test_database_if_exists()
        database_config = test_runner.setup_databases()
        yield
    finally:
        if database_config is not None:
            test_runner.teardown_databases(database_config)
        elif dropdb or not keepdb:
            drop_postgres_test_database_if_exists()
        teardown_test_environment()
