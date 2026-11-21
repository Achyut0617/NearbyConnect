from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_valid_location_returns_200():
    r = client.post("/nearby", json={"lat": 18.52, "lon": 73.85, "radius_m": 1000})
    assert r.status_code == 200
    assert r.json()["places"] == []


def test_radius_defaults_to_1000():
    r = client.post("/nearby", json={"lat": 18.52, "lon": 73.85})
    assert r.status_code == 200
    assert r.json()["radius_m"] == 1000


def test_lat_too_big_returns_422():
    r = client.post("/nearby", json={"lat": 200, "lon": 73.85, "radius_m": 1000})
    assert r.status_code == 422


def test_lon_too_small_returns_422():
    r = client.post("/nearby", json={"lat": 18.52, "lon": -181, "radius_m": 1000})
    assert r.status_code == 422


def test_zero_radius_returns_422():
    r = client.post("/nearby", json={"lat": 18.52, "lon": 73.85, "radius_m": 0})
    assert r.status_code == 422


def test_radius_too_big_returns_422():
    r = client.post("/nearby", json={"lat": 18.52, "lon": 73.85, "radius_m": 50000})
    assert r.status_code == 422


def test_missing_lat_returns_422():
    r = client.post("/nearby", json={"lon": 73.85})
    assert r.status_code == 422


def test_health_still_works():
    r = client.get("/health")
    assert r.json() == {"status": "ok"}
