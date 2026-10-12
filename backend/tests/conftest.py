"""
Pytest fixtures for the backend test suite.

Runs against a DEDICATED Postgres database (`nagham_ai_test`, created on
the same local Postgres instance docker-compose already runs for
development) -- never the real `nagham_ai` dev database. SQLite was
deliberately not used: this project's models rely on Postgres-specific
column types (pgvector's `Vector`, JSON), so a real (disposable) Postgres
database is both safer and more representative than mocking around that.

IMPORTANT: the DATABASE_URL env var must be overridden *before*
`app.database.connection` is imported anywhere (it builds its engine at
import time), which is why this happens at the very top of this file,
ahead of any `app.*` import.
"""

import os

os.environ["DATABASE_URL"] = (
    "postgresql://postgres:123456@localhost:5433/nagham_ai_test"
)
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-never-use-in-production")
# Dummy-but-well-formed Google OAuth config so app startup and the
# unauthenticated-redirect endpoints work; real network calls to Google
# are never made in this suite (tests either stay below that boundary or
# monkeypatch it explicitly).
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/auth/google/callback")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

import uuid

import pytest
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

TEST_DB_NAME = "nagham_ai_test"
ADMIN_DATABASE_URL = "postgresql://postgres:123456@localhost:5433/postgres"


def _ensure_test_database_exists() -> None:
    admin_engine = create_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": TEST_DB_NAME},
            ).first()
            if not exists:
                # TEMPLATE template0 sidesteps a template1/OS collation
                # version mismatch seen on this container image.
                conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}" TEMPLATE template0'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    _ensure_test_database_exists()

    import app.database.connection as connection_module
    import app.models  # noqa: F401 -- registers every model on Base.metadata
    from app.database.base import Base

    test_engine = create_engine(connection_module.DATABASE_URL)

    with test_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # Point the app's actual engine/session factory at the test database
    # for the whole test session, instead of constructing a second
    # parallel engine the app itself doesn't use.
    connection_module.engine = test_engine
    connection_module.SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    test_engine.dispose()


@pytest.fixture(autouse=True)
def _block_real_email_sending(monkeypatch):
    """
    Safety net: registration sends a real email via the project's actual
    Gmail SMTP credentials (from the real .env). Tests must never trigger
    that. Patched at the import site used by app.services.auth_service,
    so no test accidentally burns a real send.
    """

    import app.services.auth_service as auth_service_module

    sent = []
    monkeypatch.setattr(
        auth_service_module,
        "send_verification_email",
        lambda to_email, otp: sent.append((to_email, otp)),
    )
    yield sent


@pytest.fixture()
def db_session():
    from app.database.connection import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    from app.database.connection import get_db
    from app.main import app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


def unique_google_id() -> str:
    return f"google-test-{uuid.uuid4().hex[:16]}"
