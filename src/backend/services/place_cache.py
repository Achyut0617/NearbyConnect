"""Short-lived, in-memory cache for Overpass place lookups (step 25).

Why: public Overpass servers often take 30-60 s. People search again from
nearly the same spot (pull-to-refresh, changing interests, reopening the
app), and the places around a point don't change minute to minute.

How:
- Snap the point to a ~110 m grid (3 decimal places of lat/lon), so tiny
  GPS jitter still hits the same entry.
- Because snapping moves the centre up to ~80 m, fetch a slightly WIDER
  radius (radius + GRID_MARGIN_M). The router then drops places outside
  the user's real radius, so results stay correct.
- Entries expire after TTL_SECONDS. Oldest entries are dropped when full.
- Failures are never cached, so a busy Overpass is retried next time.

Privacy: memory only (gone on restart), coarse grid cells, nothing logged,
not tied to any user. Matches the "short-lived in-memory cache" rule.
"""

import threading
import time
from collections import OrderedDict
from typing import Callable

from services.places_provider import fetch_places_with_backup

GRID_DECIMALS = 3          # 0.001 deg lat ~ 111 m
GRID_MARGIN_M = 100        # covers the ~80 m max shift from snapping
TTL_SECONDS = 10 * 60      # places rarely change within 10 minutes
MAX_ENTRIES = 256          # small, bounded memory use

Fetcher = Callable[[float, float, int], list[dict]]


class PlaceCache:
    def __init__(self, fetch: Fetcher, ttl_seconds: float = TTL_SECONDS,
                 max_entries: int = MAX_ENTRIES,
                 clock: Callable[[], float] = time.monotonic):
        self._fetch = fetch
        self._ttl = ttl_seconds
        self._max = max_entries
        self._clock = clock
        self._entries: OrderedDict[tuple, tuple[float, list[dict]]] = OrderedDict()
        self._lock = threading.Lock()   # FastAPI runs sync routes in threads

    def __len__(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def get(self, lat: float, lon: float, radius_m: int) -> list[dict]:
        """Places around (lat, lon), from cache if fresh, else fetched.

        Raises whatever the fetcher raises (e.g. OverpassUnavailable).
        """
        snap_lat = round(lat, GRID_DECIMALS)
        snap_lon = round(lon, GRID_DECIMALS)
        key = (snap_lat, snap_lon, radius_m)
        now = self._clock()

        with self._lock:
            hit = self._entries.get(key)
            if hit is not None and now - hit[0] < self._ttl:
                self._entries.move_to_end(key)
                return list(hit[1])

        # Fetch outside the lock: it can take a long time.
        places = self._fetch(snap_lat, snap_lon, radius_m + GRID_MARGIN_M)

        with self._lock:
            self._entries[key] = (now, list(places))
            self._entries.move_to_end(key)
            while len(self._entries) > self._max:
                self._entries.popitem(last=False)   # drop the oldest
        return list(places)


# One shared cache for the running server.
# Overpass first, Geoapify backup (step 26); failures still aren't cached.
place_cache = PlaceCache(fetch_places_with_backup)


def cached_fetch_places(lat: float, lon: float, radius_m: int) -> list[dict]:
    return place_cache.get(lat, lon, radius_m)
