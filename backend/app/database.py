"""Database engine and session wiring.

The engine is created once per process and holds a connection pool. Opening a
TCP connection to Postgres costs milliseconds, so we keep a small set of them
open and hand them out per request instead of reconnecting every time.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    # pool_pre_ping sends a cheap SELECT 1 before handing out a pooled
    # connection. Without it, a connection killed by a Postgres restart or an
    # idle timeout is handed to a request and fails with a confusing error.
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class every ORM model inherits from."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one database session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
