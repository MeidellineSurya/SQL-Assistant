import os

# Set before any `app.*` import so the module-level Settings() singleton
# (app/core/config.py) and the module-level engine (app/core/database.py)
# construct successfully in CI, which has no .env file. These are
# test-only dummy values, not real secrets — the DB URL is never
# connected to by the unit tests in this package.
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-do-not-use-in-prod")
os.environ.setdefault("FERNET_KEY", "7kSxBGCsrp-ADe5Qw1T5bFQlvVkz6HFArIbwoVq4b7A=")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
