"""Tests for services/place_cache.py (step 25: cache Overpass results)."""

import pytest

from services.osm_client import OverpassUnavailable
from services.place_cache import GRID_MARGIN_M, PlaceCache


class FakeClock:
    """A clock we can move forward by hand, so TTL tests don't need sleep()."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def counting_fetcher(result=None):
    calls = []

    def fetch(lat, lon, radius_m):
        calls.append((lat, lon, radius_m))
        return list(result or [{"name": "Cafe", "lat": lat, "lon": lon}])

    return fetch, calls


def test_second_lookup_from_same_spot_uses_cache():
    fetch, calls = counting_fetcher()
    cache = PlaceCache(fetch)
    cache.get(18.5204, 73.8567, 1000)
    cache.get(18.5204, 73.8567, 1000)
    assert len(calls) == 1


def test_nearby_point_in_same_grid_cell_reuses_result():
    fetch, calls = counting_fetcher()
    cache = PlaceCache(fetch)
    cache.get(18.52041, 73.85671, 1000)
    cache.get(18.52044, 73.85674, 1000)   # a few metres away
    assert len(calls) == 1


def test_far_point_fetches_again():
    fetch, calls = counting_fetcher()
    cache = PlaceCache(fetch)
    cache.get(18.5204, 73.8567, 1000)
    cache.get(18.6000, 73.9000, 1000)
    assert len(calls) == 2


def test_different_radius_fetches_again():
    fetch, calls = counting_fetcher()
    cache = PlaceCache(fetch)
    cache.get(18.5204, 73.8567, 1000)
    cache.get(18.5204, 73.8567, 3000)
    assert len(calls) == 2


def test_fetch_uses_snapped_point_and_widened_radius():
    """Snapping moves the centre a little, so we search a bit wider to cover
    the user's full circle."""
    fetch, calls = counting_fetcher()
    PlaceCache(fetch).get(18.52041, 73.85671, 1000)
    lat, lon, radius = calls[0]
    assert (lat, lon) == (18.520, 73.857)
    assert radius == 1000 + GRID_MARGIN_M


def test_entry_expires_after_ttl():
    fetch, calls = counting_fetcher()
    clock = FakeClock()
    cache = PlaceCache(fetch, ttl_seconds=600, clock=clock)
    cache.get(18.52, 73.85, 1000)
    clock.now += 599
    cache.get(18.52, 73.85, 1000)
    assert len(calls) == 1
    clock.now += 2
    cache.get(18.52, 73.85, 1000)
    assert len(calls) == 2


def test_failures_are_not_cached():
    attempts = []

    def flaky(lat, lon, radius_m):
        attempts.append(1)
        if len(attempts) == 1:
            raise OverpassUnavailable("busy")
        return [{"name": "Cafe", "lat": lat, "lon": lon}]

    cache = PlaceCache(flaky)
    with pytest.raises(OverpassUnavailable):
        cache.get(18.52, 73.85, 1000)
    assert cache.get(18.52, 73.85, 1000)[0]["name"] == "Cafe"
    assert len(attempts) == 2


def test_oldest_entry_dropped_when_full():
    fetch, calls = counting_fetcher()
    cache = PlaceCache(fetch, max_entries=2)
    cache.get(10.0, 10.0, 1000)
    cache.get(20.0, 20.0, 1000)
    cache.get(30.0, 30.0, 1000)          # pushes out (10, 10)
    assert len(cache) == 2
    cache.get(10.0, 10.0, 1000)
    assert len(calls) == 4


def test_callers_cannot_corrupt_cached_list():
    fetch, _ = counting_fetcher()
    cache = PlaceCache(fetch)
    first = cache.get(18.52, 73.85, 1000)
    first.clear()
    first_again = cache.get(18.52, 73.85, 1000)
    assert len(first_again) == 1


def test_clear_empties_cache():
    fetch, calls = counting_fetcher()
    cache = PlaceCache(fetch)
    cache.get(18.52, 73.85, 1000)
    cache.clear()
    cache.get(18.52, 73.85, 1000)
    assert len(calls) == 2


def test_shared_cache_uses_the_backup_provider():
    from services.place_cache import place_cache
    from services.places_provider import fetch_places_with_backup
    assert place_cache._fetch is fetch_places_with_backup
