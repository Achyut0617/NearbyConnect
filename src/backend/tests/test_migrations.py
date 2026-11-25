"""Tests for the Alembic migrations (step 27).

Each test builds a brand-new SQLite file in a temp folder, so it never
touches the shared in-memory test database.
"""

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

import models  # noqa: F401
from db import Base

BACKEND = Path(__file__).resolve().parents[1]


def run(cmd, db_file, *args):
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "migrations"))
    engine = create_engine(f"sqlite:///{db_file}")
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        getattr(command, cmd)(cfg, *args)
    return engine


def test_upgrade_builds_exactly_what_the_models_describe(tmp_path):
    engine = run("upgrade", tmp_path / "t.db", "head")
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == [], f"models and migrations disagree: {diff}"


def test_downgrade_removes_every_table(tmp_path):
    db = tmp_path / "t.db"
    run("upgrade", db, "head")
    engine = run("downgrade", db, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}


def test_upgrade_twice_is_safe(tmp_path):
    db = tmp_path / "t.db"
    run("upgrade", db, "head")
    engine = run("upgrade", db, "head")
    assert {"users", "connect_requests"} <= set(inspect(engine).get_table_names())
