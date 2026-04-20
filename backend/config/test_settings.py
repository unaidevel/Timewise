from config.settings import *  # noqa: F403

SECRET_KEY = "test-secret-key"
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver", "testclient"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
