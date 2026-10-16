"""Shared pytest fixtures.

Strategy: one throwaway Postgres database for the whole test session, created
and dropped around the run. Inside it, every single test runs in a transaction
that is rolled back when the test ends.

Why a rollback and not DELETE FROM: a rollback is instant, it cannot miss a
table someone added later, and it leaves sequences and enum types untouched.
The result is that tests are hermetic -- each one sees an empty database no
matter what any other test did, and no matter what order they ran in.
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Point at the admin database so we can CREATE DATABASE for the test run.
ADMIN_URL = os.getenv(
    "TEST_ADMIN_URL", "postgresql+psycopg://taskr:taskr@localhost:5433/postgres"
)
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "taskr_test")
TEST_URL = ADMIN_URL.rsplit("/", 1)[0] + f"/{TEST_DB_NAME}"

# Set before importing the app so its engine is built against the test database.
os.environ["DATABASE_URL"] = TEST_URL

from app import models  # noqa: E402,F401 - registers tables on Base.metadata
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def test_engine():
    """Create a dedicated test database, build the schema, drop it at the end."""
    # isolation_level AUTOCOMMIT: CREATE DATABASE cannot run inside a transaction.
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))

    engine = create_engine(TEST_URL)
    Base.metadata.create_all(engine)
    yield engine

    engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture
def db_session(test_engine) -> Session:
    """One transaction per test, rolled back afterwards.

    The session is bound to an explicit connection with an open transaction.
    Anything the test wrote -- even through a commit in application code --
    disappears when we roll the outer transaction back.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session) -> TestClient:
    """A test client whose requests use the rolled-back session.

    This is the dependency override: the routes still call Depends(get_db), but
    FastAPI now resolves it to our test session. No application code changes.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_task(client) -> dict:
    """A task that already exists, for tests about reading and changing one."""
    response = client.post(
        "/api/tasks",
        json={"title": "Seeded task", "priority": "high", "status": "todo"},
    )
    assert response.status_code == 201
    return response.json()
