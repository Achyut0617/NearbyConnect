"""Shared test setup. pytest loads this file automatically before the tests.

Tests use a fresh in-memory SQLite database, so they never touch real data.
"""

import os

# Must be set BEFORE `db` is imported anywhere.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402

from db import Base, engine  # noqa: E402
import models  # noqa: E402,F401


@pytest.fixture(autouse=True)
def fresh_db():
    """Empty database for every single test."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.fixture
def make_user(client):
    """Create a user and return (id, auth_headers)."""
    def _make(name="Test User", interests=None):
        r = client.post("/users", json={"display_name": name})
        assert r.status_code == 201
        data = r.json()
        headers = {"Authorization": f"Bearer {data['token']}"}
        if interests is not None:
            r = client.put("/me/interests", json={"interests": interests}, headers=headers)
            assert r.status_code == 200
        return data["id"], headers
    return _make
