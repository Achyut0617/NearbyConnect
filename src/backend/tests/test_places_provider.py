"""Tests for services/places_provider.py (Overpass -> Geoapify backup, step 26)."""

import pytest

from services.geoapify_client import GeoapifyUnavailable
from services.osm_client import OverpassUnavailable
from services.places_provider import make_fallback_fetcher

PLACE = [{"osm_id": "n/1", "name": "Cafe", "type_key": "amenity", "type": "cafe",
          "lat": 18.5, "lon": 73.8}]


def failing(exc):
    def fetch(lat, lon, r):
        raise exc
    return fetch


def test_primary_success_never_calls_backup():
    calls = []
    fetch = make_fallback_fetcher(lambda *a: PLACE, lambda *a: calls.append(a) or [])
    assert fetch(18.5, 73.8, 500) == PLACE
    assert calls == []


def test_backup_used_when_overpass_is_down():
    fetch = make_fallback_fetcher(failing(OverpassUnavailable("busy")), lambda *a: PLACE)
    assert fetch(18.5, 73.8, 500) == PLACE


def test_both_failing_raises_overpass_unavailable():
    fetch = make_fallback_fetcher(failing(OverpassUnavailable("busy")),
                                  failing(GeoapifyUnavailable("no key")))
    with pytest.raises(OverpassUnavailable, match="backup also failed: no key"):
        fetch(18.5, 73.8, 500)


def test_unexpected_errors_are_not_hidden():
    fetch = make_fallback_fetcher(failing(ValueError("bug")), lambda *a: PLACE)
    with pytest.raises(ValueError):
        fetch(18.5, 73.8, 500)
