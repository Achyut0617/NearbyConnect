"""Fetch nearby places from OpenStreetMap using the free Overpass API.

Overpass is a free, shared service run by volunteers, so we:
- send ONE request per search (no hammering),
- give each server a time limit,
- try a few public servers in turn if one is busy,
- identify ourselves with a generic User-Agent (no personal info).

Privacy: we never log the coordinates we are asked about.
"""

import httpx

# Public Overpass servers, tried in this order.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# OSM "tag keys" that describe what kind of place something is.
# e.g. amenity=cafe, shop=books, leisure=park, tourism=museum, office=coworking
PLACE_KEYS = ("amenity", "shop", "leisure", "tourism", "office")

USER_AGENT = "NearbyConnect/0.1 (dev)"
TIMEOUT_SECONDS = 25   # per server
MAX_RESULTS = 200      # keep responses small and fair to the free service


class OverpassUnavailable(Exception):
    """Raised when every Overpass server failed (busy, timed out, or broken)."""


def build_query(lat: float, lon: float, radius_m: int) -> str:
    """Build an Overpass QL query for named places within radius_m of (lat, lon).

    `nwr` = nodes, ways and relations (points, outlines and groups).
    `out center` gives a single centre point even for buildings/areas.
    """
    around = f"(around:{radius_m},{lat},{lon})"
    lines = [f'  nwr["name"]["{key}"]{around};' for key in PLACE_KEYS]
    return (
        f"[out:json][timeout:{TIMEOUT_SECONDS}];\n"
        "(\n" + "\n".join(lines) + "\n);\n"
        f"out center {MAX_RESULTS};"
    )


def parse_elements(data: dict) -> list[dict]:
    """Turn Overpass's raw JSON into a simple list of places.

    Each place: {"osm_id", "name", "type_key", "type", "lat", "lon"}
    Entries with no name, no recognised type, or no coordinates are skipped.
    """
    places = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        # Find the first tag that tells us what kind of place this is.
        type_key = next((k for k in PLACE_KEYS if k in tags), None)
        if type_key is None:
            continue

        # Points have lat/lon directly; areas have them under "center".
        point = el if "lat" in el else el.get("center", {})
        if "lat" not in point or "lon" not in point:
            continue

        places.append({
            "osm_id": f"{el.get('type')}/{el.get('id')}",
            "name": name,
            "type_key": type_key,
            "type": tags[type_key],
            "lat": point["lat"],
            "lon": point["lon"],
        })
    return places


def fetch_places(lat: float, lon: float, radius_m: int,
                 client: httpx.Client | None = None) -> list[dict]:
    """Ask Overpass for named places near (lat, lon). Returns a list of places.

    `client` lets tests pass in a fake HTTP client; normally leave it as None.
    Raises OverpassUnavailable if every server fails.
    """
    query = build_query(lat, lon, radius_m)
    own_client = client is None
    if own_client:
        client = httpx.Client(timeout=TIMEOUT_SECONDS + 5,
                              headers={"User-Agent": USER_AGENT})

    problems = []
    try:
        for url in OVERPASS_URLS:
            try:
                resp = client.post(url, data={"data": query})
            except httpx.HTTPError as e:            # timeout, connection refused...
                problems.append(f"{url}: {type(e).__name__}")
                continue

            if resp.status_code != 200:              # 429 too many requests, 504 busy...
                problems.append(f"{url}: HTTP {resp.status_code}")
                continue

            try:
                data = resp.json()
            except ValueError:                       # got an HTML error page, not JSON
                problems.append(f"{url}: response was not JSON")
                continue

            # Overpass sometimes says 200 OK but includes a runtime error "remark".
            remark = data.get("remark", "")
            if "error" in remark.lower():
                problems.append(f"{url}: server remark: {remark[:80]}")
                continue

            return parse_elements(data)
    finally:
        if own_client:
            client.close()

    raise OverpassUnavailable("All Overpass servers failed: " + "; ".join(problems))
