"""Tests for services/osm_client.py.

Most tests use a FAKE Overpass server (httpx.MockTransport), so they are
fast and work offline. The one test marked `network` hits the real servers;
run it with:  pytest -m network
"""

import httpx
import pytest

from services.osm_client import (
    OVERPASS_URLS,
    OverpassUnavailable,
    build_query,
    fetch_places,
    parse_elements,
)

# A small, realistic sample of what Overpass returns.
SAMPLE = {
    "elements": [
        # A point (node) with lat/lon directly on it.
        {"type": "node", "id": 1, "lat": 18.52, "lon": 73.85,
         "tags": {"name": "Cafe Good Luck", "amenity": "cafe"}},
        # A building (way): coordinates are under "center".
        {"type": "way", "id": 2, "center": {"lat": 18.53, "lon": 73.86},
         "tags": {"name": "City Library", "amenity": "library"}},
        # No name -> should be skipped.
        {"type": "node", "id": 3, "lat": 18.5, "lon": 73.8,
         "tags": {"amenity": "bench"}},
        # Name but no place-type tag -> skipped.
        {"type": "node", "id": 4, "lat": 18.5, "lon": 73.8,
         "tags": {"name": "Some Street Sign"}},
        # No coordinates at all -> skipped.
        {"type": "way", "id": 5, "tags": {"name": "Ghost Shop", "shop": "books"}},
    ]
}


def fake_client(handler):
    """An httpx client that sends requests to `handler` instead of the internet."""
    return httpx.Client(transport=httpx.MockTransport(handler))


# ---------- build_query ----------

def test_query_contains_location_and_radius():
    q = build_query(18.52, 73.85, 1000)
    assert "around:1000,18.52,73.85" in q
    assert '["amenity"]' in q and '["shop"]' in q
    assert "[out:json]" in q


# ---------- parse_elements ----------

def test_parse_keeps_only_good_places():
    places = parse_elements(SAMPLE)
    assert [p["name"] for p in places] == ["Cafe Good Luck", "City Library"]


def test_parse_reads_center_for_buildings():
    library = parse_elements(SAMPLE)[1]
    assert (library["lat"], library["lon"]) == (18.53, 73.86)
    assert library["type_key"] == "amenity"
    assert library["type"] == "library"
    assert library["osm_id"] == "way/2"


def test_parse_empty_response():
    assert parse_elements({}) == []


# ---------- fetch_places (fake server) ----------

def test_fetch_success_on_first_server():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(200, json=SAMPLE)

    places = fetch_places(18.52, 73.85, 1000, client=fake_client(handler))
    assert len(places) == 2
    assert len(calls) == 1  # didn't bother the other servers


def test_fetch_falls_back_when_first_server_busy():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        if str(request.url) == OVERPASS_URLS[0]:
            return httpx.Response(504, text="<html>too busy</html>")
        return httpx.Response(200, json=SAMPLE)

    places = fetch_places(18.52, 73.85, 1000, client=fake_client(handler))
    assert len(places) == 2
    assert calls == OVERPASS_URLS[:2]


def test_fetch_falls_back_on_timeout():
    def handler(request):
        if str(request.url) == OVERPASS_URLS[0]:
            raise httpx.ReadTimeout("slow", request=request)
        return httpx.Response(200, json=SAMPLE)

    assert len(fetch_places(18.52, 73.85, 1000, client=fake_client(handler))) == 2


def test_fetch_treats_runtime_remark_as_failure():
    def handler(request):
        if str(request.url) == OVERPASS_URLS[0]:
            return httpx.Response(200, json={
                "elements": [],
                "remark": "runtime error: Query timed out",
            })
        return httpx.Response(200, json=SAMPLE)

    assert len(fetch_places(18.52, 73.85, 1000, client=fake_client(handler))) == 2


def test_fetch_raises_when_all_servers_fail():
    def handler(request):
        return httpx.Response(504, text="<html>too busy</html>")

    with pytest.raises(OverpassUnavailable) as err:
        fetch_places(18.52, 73.85, 1000, client=fake_client(handler))
    assert "HTTP 504" in str(err.value)


def test_error_message_does_not_contain_coordinates():
    # Privacy: errors may end up in logs, so they must not include location.
    def handler(request):
        return httpx.Response(504)

    with pytest.raises(OverpassUnavailable) as err:
        fetch_places(18.5195, 73.8553, 1000, client=fake_client(handler))
    assert "18.5195" not in str(err.value)
    assert "73.8553" not in str(err.value)


# ---------- real internet (opt-in) ----------

@pytest.mark.network
def test_real_overpass_finds_places_near_landmark():
    # Shaniwar Wada, Pune: a busy old-city area with many named places.
    places = fetch_places(18.5195, 73.8553, 500)
    assert len(places) > 0
