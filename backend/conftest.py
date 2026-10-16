"""Pytest fixtures shared by every test.

The whole point of this file: the tests must never touch the real Postgres.

FastAPI resolves `Depends(get_db)` through a lookup table on the app object, so
overriding that entry swaps the database out from under the application without
the application code knowing anything about it. That is dependency injection
doing real work -- no test flag, no `if TESTING:` branch in production code.

Each test gets its own in-memory SQLite database, created before the test and
thrown away after. Tests therefore cannot leak rows into each other, which is
what keeps the suite from going flaky when CI changes the execution order.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importing models registers the tables on Base.metadata. Without this import
# create_all() would produce an empty database and every test would 500.
# Note the `from app import models` form: plain `import app.models` would rebind
# the local name `app` from the FastAPI instance to the package, and every
# `app.dependency_overrides` below would fail with AttributeError.
from app import models  # noqa: F401
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    """A fresh, empty database for one test."""
    engine = create_engine(
        "sqlite://",  # :memory:
        connect_args={"check_same_thread": False},
        # TestClient runs requests on a different thread than the fixture. The
        # default pool would hand that thread a *different* in-memory database
        # (each SQLite memory connection is its own database). StaticPool
        # reuses the single connection, so test and app see the same data.
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """An HTTP client talking to the real app, backed by the throwaway database."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    # Always clear the override, or it leaks into any later test that wanted
    # the real dependency.
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_task(client):
    """One task already in the database, for tests that need an existing row."""
    response = client.post(
        "/api/tasks",
        json={"title": "Write the Helm chart", "priority": "high", "status": "todo"},
    )
    assert response.status_code == 201
    return response.json()
