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
    # Used by tests; the real server uses migrate_database() instead.
    import models  # noqa: F401
    Base.metadata.create_all(engine)


def migrate_database(target_engine=None) -> str:
    """Bring the database up to the latest migration (step 27).

    - Empty database          -> run every migration ("upgraded").
    - Made before step 27 by create_all (tables exist, no alembic_version)
                              -> mark it as version 0001 first ("adopted"),
                                 then apply any newer migrations. No data lost.
    - Already managed         -> apply only the new migrations ("upgraded").
    """
    from pathlib import Path

    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    target_engine = target_engine or engine
    here = Path(__file__).resolve().parent
    cfg = Config(str(here / "alembic.ini"))
    cfg.set_main_option("script_location", str(here / "migrations"))

    tables = set(inspect(target_engine).get_table_names())
    adopted = "users" in tables and "alembic_version" not in tables
    with target_engine.begin() as conn:
        cfg.attributes["connection"] = conn
        if adopted:
            command.stamp(cfg, "0001")
        command.upgrade(cfg, "head")
    return "adopted" if adopted else "upgraded"
