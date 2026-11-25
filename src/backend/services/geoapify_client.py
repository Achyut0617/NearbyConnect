"""Backup places provider: Geoapify Places API (step 26).

Geoapify serves the same OpenStreetMap data as Overpass, but from paid,
reliable servers with a free tier (needs a free key: GEOAPIFY_API_KEY).
We only use it when every Overpass server has failed.

Results are converted to the SAME shape osm_client returns, so the rest
of the app (clean, score, rank) does not care where places came from:
    {"osm_id", "name", "type_key", "type", "lat", "lon"}

Privacy: like osm_client, we never log the coordinates we are asked about.
"""

import os

import httpx

API_URL = "https://api.geoapify.com/v2/places"
TIMEOUT_SECONDS = 15
MAX_RESULTS = 200   # same cap as osm_client


class GeoapifyUnavailable(Exception):
    """No key configured, or the Geoapify request failed."""


# Geoapify category -> (OSM tag key, OSM tag value).
# Only categories we can map cleanly; others are skipped.
CATEGORY_MAP: dict[str, tuple[str, str]] = {
    "catering.cafe": ("amenity", "cafe"),
    "catering.restaurant": ("amenity", "restaurant"),
    "catering.fast_food": ("amenity", "fast_food"),
    "catering.bar": ("amenity", "bar"),
    "catering.pub": ("amenity", "pub"),
    "education.library": ("amenity", "library"),
    "education.university": ("amenity", "university"),
    "education.college": ("amenity", "college"),
    "education.school": ("amenity", "school"),
    "commercial.books": ("shop", "books"),
    "commercial.supermarket": ("shop", "supermarket"),
    "commercial.marketplace": ("amenity", "marketplace"),
    "leisure.park": ("leisure", "park"),
    "sport.fitness": ("leisure", "fitness_centre"),
    "sport.sports_centre": ("leisure", "sports_centre"),
    "entertainment.museum": ("tourism", "museum"),
    "entertainment.cinema": ("amenity", "cinema"),
    "entertainment.culture.theatre": ("amenity", "theatre"),
    "entertainment.culture.arts_centre": ("amenity", "arts_centre"),
    "tourism.attraction": ("tourism", "attraction"),
    "tourism.sights.place_of_worship": ("amenity", "place_of_worship"),
    "tourism.sights.fort": ("historic", "fort"),
    "office.coworking": ("office", "coworking"),
    "office.company": ("office", "company"),
    "healthcare.hospital": ("amenity", "hospital"),
    "healthcare.pharmacy": ("amenity", "pharmacy"),
}

# The categories we ask Geoapify for (it needs an explicit list).
REQUEST_CATEGORIES = sorted({c.split(".")[0] for c in CATEGORY_MAP} | {
    "office", "sport", "tourism"})


def osm_type_for(categories: list[str]) -> tuple[str, str] | None:
    """Pick the most specific mapped category, e.g. 'catering.cafe' over 'catering'."""
    for cat in sorted(categories, key=lambda c: c.count("."), reverse=True):
        if cat in CATEGORY_MAP:
            return CATEGORY_MAP[cat]
    return None


def parse_features(data: dict) -> list[dict]:
    """Turn Geoapify's GeoJSON into the same place list osm_client returns.

    Features with no name, no mappable category or no coordinates are skipped.
    """
    places = []
    for feat in data.get("features", []):
        props = feat.get("properties") or {}
        name = props.get("name")
        if not name:
            continue
        osm_type = osm_type_for(props.get("categories") or [])
        if osm_type is None:
            continue
        lat, lon = props.get("lat"), props.get("lon")
        if lat is None or lon is None:
            coords = (feat.get("geometry") or {}).get("coordinates") or []
            if len(coords) != 2:
                continue
            lon, lat = coords   # GeoJSON order is [lon, lat]
        osm = (props.get("datasource") or {}).get("raw") or {}
        osm_id = (f"{osm.get('osm_type', 'n')}/{osm['osm_id']}" if "osm_id" in osm
                  else f"geoapify/{props.get('place_id', name)}")
        places.append({
            "osm_id": osm_id,
            "name": name,
            "type_key": osm_type[0],
            "type": osm_type[1],
            "lat": lat,
            "lon": lon,
        })
    return places


def fetch_places(lat: float, lon: float, radius_m: int,
                 client: httpx.Client | None = None,
                 api_key: str | None = None) -> list[dict]:
    """Ask Geoapify for named places near (lat, lon).

    Raises GeoapifyUnavailable if no key is set or the request fails.
    `client` and `api_key` let tests pass fakes; normally leave them as None.
    """
    key = api_key if api_key is not None else os.getenv("GEOAPIFY_API_KEY", "")
    if not key:
        raise GeoapifyUnavailable("GEOAPIFY_API_KEY is not set")
    params = {
        "categories": ",".join(REQUEST_CATEGORIES),
        "filter": f"circle:{lon},{lat},{radius_m}",   # Geoapify wants lon first
        "limit": MAX_RESULTS,
        "apiKey": key,
    }
    own_client = client is None
    if own_client:
        client = httpx.Client(timeout=TIMEOUT_SECONDS)
    try:
        try:
            resp = client.get(API_URL, params=params)
        except httpx.HTTPError as e:
            raise GeoapifyUnavailable(f"request failed: {type(e).__name__}") from e
        if resp.status_code != 200:
            raise GeoapifyUnavailable(f"HTTP {resp.status_code}")
        try:
            data = resp.json()
        except ValueError as e:
            raise GeoapifyUnavailable("response was not JSON") from e
        return parse_features(data)
    finally:
        if own_client:
            client.close()
