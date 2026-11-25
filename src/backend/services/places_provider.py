"""Places with a backup (step 26): Overpass first, Geoapify if it fails.

If Overpass works, Geoapify is never called. If Overpass fails and no
Geoapify key is set (or Geoapify fails too), we raise OverpassUnavailable,
so /nearby keeps returning its friendly 503 exactly as before.
"""

from typing import Callable

from services import geoapify_client, osm_client
from services.osm_client import OverpassUnavailable

Fetcher = Callable[[float, float, int], list[dict]]


def make_fallback_fetcher(primary: Fetcher, backup: Fetcher) -> Fetcher:
    def fetch(lat: float, lon: float, radius_m: int) -> list[dict]:
        try:
            return primary(lat, lon, radius_m)
        except OverpassUnavailable as first:
            try:
                return backup(lat, lon, radius_m)
            except geoapify_client.GeoapifyUnavailable as second:
                raise OverpassUnavailable(
                    f"{first}; backup also failed: {second}") from second
    return fetch


fetch_places_with_backup = make_fallback_fetcher(
    lambda lat, lon, r: osm_client.fetch_places(lat, lon, r),
    lambda lat, lon, r: geoapify_client.fetch_places(lat, lon, r),
)
