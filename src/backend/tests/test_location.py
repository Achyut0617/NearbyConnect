"""Tests for POST /nearby (Steps 2 and 7).

The real Overpass fetch is replaced with a fake, so these run offline.
"""

import pytest

from main import app
from routers.location import get_place_fetcher
from services.osm_client import OverpassUnavailable

USER_LAT, USER_LON = 18.5200, 73.8500

FAKE_RAW = [
    {"osm_id": "node/1", "name": "Vaishali", "type_key": "amenity",
     "type": "restaurant", "lat": 18.5201, "lon": 73.8500},
    {"osm_id": "node/2", "name": "91springboard", "type_key": "office",
     "type": "coworking", "lat": 18.5250, "lon": 73.8500},
    {"osm_id": "node/3", "name": "Central Library", "type_key": "amenity",
     "type": "library", "lat": 18.5230, "lon": 73.8500},
    {"osm_id": "node/4", "name": "   ", "type_key": "amenity",          # dropped by cleaning
     "type": "cafe", "lat": 18.5202, "lon": 73.8500},
]


@pytest.fixture(autouse=True)
def fake_fetch():
    """Use FAKE_RAW instead of calling the internet. Records calls."""
    calls = []

    def fake(lat, lon, radius_m):
        calls.append((lat, lon, radius_m))
        return FAKE_RAW

    app.dependency_overrides[get_place_fetcher] = lambda: fake
    yield calls
    app.dependency_overrides.pop(get_place_fetcher, None)


def post(client, headers=None, **body):
    body = {"lat": USER_LAT, "lon": USER_LON, **body}
    return client.post("/nearby", json=body, headers=headers or {})


# ---------- validation (Step 2) ----------

def test_valid_location_returns_200(client):
    assert post(client, radius_m=1000).status_code == 200


def test_radius_defaults_to_1000(client, fake_fetch):
    assert post(client).json()["radius_m"] == 1000
    assert fake_fetch[0][2] == 1000


@pytest.mark.parametrize("body", [
    {"lat": 200}, {"lon": -181}, {"radius_m": 0}, {"radius_m": 50000},
    {"limit": 0}, {"interests": ["x" * 41]},
])
def test_bad_input_returns_422(client, body):
    assert post(client, **body).status_code == 422


def test_missing_lat_returns_422(client):
    assert client.post("/nearby", json={"lon": 73.85}).status_code == 422


def test_health_still_works(client):
    assert client.get("/health").json() == {"status": "ok"}


# ---------- full pipeline (Step 7) ----------

def test_places_are_cleaned_and_ranked_by_interest(client):
    data = post(client, interests=["startups"]).json()
    names = [p["name"] for p in data["places"]]
    assert names[0] == "91springboard"           # coworking matches startups
    assert len(names) == 3                       # blank-name entry removed
    top = data["places"][0]
    assert top["category"] == "coworking"
    assert top["score"] > 0 and top["reasons"]
    assert top["distance_m"] > 0


def test_no_interests_sorted_by_distance(client):
    data = post(client).json()
    assert data["interests_used"] == []
    assert [p["name"] for p in data["places"]] == ["Vaishali", "Central Library", "91springboard"]


def test_uses_saved_interests_when_logged_in(client, make_user):
    _, headers = make_user(interests=["reading"])
    data = post(client, headers=headers).json()
    assert data["interests_used"] == ["reading"]
    assert data["places"][0]["name"] == "Central Library"


def test_body_interests_override_saved(client, make_user):
    _, headers = make_user(interests=["reading"])
    data = post(client, headers=headers, interests=["Startups"]).json()
    assert data["interests_used"] == ["startups"]
    assert data["places"][0]["name"] == "91springboard"


def test_limit(client):
    data = post(client, limit=1).json()
    assert data["count"] == 1 and len(data["places"]) == 1


def test_overpass_down_returns_503(client):
    def broken(lat, lon, radius_m):
        raise OverpassUnavailable("all servers busy")

    app.dependency_overrides[get_place_fetcher] = lambda: broken
    r = post(client)
    assert r.status_code == 503
    assert "try again" in r.json()["detail"]


def test_cors_preflight_allows_browser_app(client):
    r = client.options("/nearby", headers={
        "Origin": "http://localhost:8081",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    })
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") in ("*", "http://localhost:8081")
