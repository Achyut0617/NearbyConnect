"""Database setup.

DATABASE_URL decides which database we use:
- not set  -> a local SQLite file (nearbyconnect.db). No setup needed.
- set      -> e.g. postgresql+psycopg://user:password@localhost:5432/nearbyconnect

The same code works with both, thanks to SQLAlchemy.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nearbyconnect.db")


def _make_engine(url: str):
    if url.startswith("sqlite"):
        kwargs = {"connect_args": {"check_same_thread": False}}
        if url in ("sqlite://", "sqlite:///:memory:"):
            # In-memory DB (used by tests): share one connection so data persists.
            kwargs["poolclass"] = StaticPool
        return create_engine(url, **kwargs)
    return create_engine(url, pool_pre_ping=True)


engine = _make_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent class for all database tables."""


def get_db():
    """FastAPI dependency: open a DB session for one request, then close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    # Import models so SQLAlchemy knows about every table before creating them.
    import models  # noqa: F401
    Base.metadata.create_all(engine)
