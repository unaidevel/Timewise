import pytest


@pytest.fixture(scope="session", autouse=True)
def django_test_environment():
    """No-op override: architecture tests are pure AST checks, no DB needed."""
    yield
