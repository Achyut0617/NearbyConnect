"""Tests for location opt-in and storage (Step 8)."""

from datetime import timedelta

from db import SessionLocal
from models.user import User, utcnow
from routers.sharing import is_fresh


def stored(user_id):
    """Read what's really in the database for this user."""
    with SessionLocal() as db:
        u = db.get(User, user_id)
        return u.share_location, u.last_lat, u.last_lon, u.location_updated_at


def test_consent_true_stores_location(client, make_user):
    uid, h = make_user()
    r = client.put("/me/location", json={"consent": True, "lat": 18.52, "lon": 73.85}, headers=h)
    assert r.status_code == 200
    assert r.json()["sharing"] is True and r.json()["fresh"] is True
    sharing, lat, lon, updated = stored(uid)
    assert (sharing, lat, lon) == (True, 18.52, 73.85)
    assert updated is not None


def test_consent_false_stores_nothing_even_if_coords_sent(client, make_user):
    # The Step 8 "false case" from PLAN.md.
    uid, h = make_user()
    r = client.put("/me/location", json={"consent": False, "lat": 18.52, "lon": 73.85}, headers=h)
    assert r.status_code == 200
    assert r.json() == {"sharing": False, "updated_at": None, "fresh": False}
    assert stored(uid) == (False, None, None, None)


def test_turning_consent_off_erases_location(client, make_user):
    uid, h = make_user()
    client.put("/me/location", json={"consent": True, "lat": 18.52, "lon": 73.85}, headers=h)
    client.put("/me/location", json={"consent": False}, headers=h)
    assert stored(uid) == (False, None, None, None)


def test_delete_erases_location(client, make_user):
    uid, h = make_user()
    client.put("/me/location", json={"consent": True, "lat": 18.52, "lon": 73.85}, headers=h)
    assert client.delete("/me/location", headers=h).json()["sharing"] is False
    assert stored(uid) == (False, None, None, None)


def test_only_last_location_is_kept(client, make_user):
    uid, h = make_user()
    client.put("/me/location", json={"consent": True, "lat": 18.52, "lon": 73.85}, headers=h)
    client.put("/me/location", json={"consent": True, "lat": 19.07, "lon": 72.87}, headers=h)
    _, lat, lon, _ = stored(uid)
    assert (lat, lon) == (19.07, 72.87)


def test_consent_true_needs_coordinates(client, make_user):
    _, h = make_user()
    assert client.put("/me/location", json={"consent": True}, headers=h).status_code == 422
    assert client.put("/me/location", json={"consent": True, "lat": 18.5}, headers=h).status_code == 422


def test_bad_coordinates_rejected(client, make_user):
    _, h = make_user()
    r = client.put("/me/location", json={"consent": True, "lat": 200, "lon": 73.85}, headers=h)
    assert r.status_code == 422


def test_requires_login(client):
    assert client.put("/me/location", json={"consent": False}).status_code == 401
    assert client.get("/me/location").status_code == 401


def test_status_does_not_echo_coordinates(client, make_user):
    _, h = make_user()
    client.put("/me/location", json={"consent": True, "lat": 18.52, "lon": 73.85}, headers=h)
    body = client.get("/me/location", headers=h).json()
    assert "lat" not in body and "lon" not in body


def test_new_users_are_not_sharing(client, make_user):
    uid, h = make_user()
    assert stored(uid) == (False, None, None, None)


def test_is_fresh_rules():
    u = User(share_location=True, last_lat=1.0, last_lon=1.0, location_updated_at=utcnow())
    assert is_fresh(u)
    u.location_updated_at = utcnow() - timedelta(hours=3)
    assert not is_fresh(u)                     # too old
    u.location_updated_at = utcnow()
    u.share_location = False
    assert not is_fresh(u)                     # not sharing
