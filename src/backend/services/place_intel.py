"""Stage A (Step 15): look up a place from trusted public sources.

Sources (all free, official REST APIs, no key needed):
- Nominatim (OpenStreetMap): turn a place NAME into coordinates + address parts.
- Wikipedia REST: a short, trusted summary of the place.
- Wikidata: structured facts (what it is, what it's near).

Design: the HTTP client is injectable so tests run OFFLINE with sample data.
Privacy: this is about PLACES, never people. Nothing is stored long-term.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import httpx

USER_AGENT = "NearbyConnect/0.1 (educational project; contact via app)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
TIMEOUT_SECONDS = 15


class PlaceNotFound(Exception):
    """Raised when no trusted source recognises the place name."""


@dataclass
class PlaceFacts:
    query: str
    name: str | None = None
    lat: float | None = None
    lon: float | None = None
    place_type: str | None = None          # e.g. "village", "suburb", "city"
    district: str | None = None
    state: str | None = None
    country: str | None = None
    summary: str | None = None             # from Wikipedia
    wikipedia_title: str | None = None
    landmarks: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _client(client: httpx.Client | None) -> tuple[httpx.Client, bool]:
    if client is not None:
        return client, False
    return httpx.Client(timeout=TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}), True


def geocode(query: str, client: httpx.Client | None = None) -> dict | None:
    """Nominatim: name -> one best match with coordinates + address parts."""
    c, owned = _client(client)
    try:
        resp = c.get(
            NOMINATIM_URL,
            params={"q": query, "format": "jsonv2", "addressdetails": 1, "limit": 1},
            headers={"User-Agent": USER_AGENT},
        )
        if resp.status_code != 200:
            return None
        results = resp.json()
        return results[0] if results else None
    except (httpx.HTTPError, ValueError):
        return None
    finally:
        if owned:
            c.close()


def wiki_summary(title: str, client: httpx.Client | None = None) -> dict | None:
    """Wikipedia REST: a short trusted summary for a page title."""
    c, owned = _client(client)
    try:
        resp = c.get(
            WIKI_SUMMARY_URL.format(title=title.replace(" ", "_")),
            headers={"User-Agent": USER_AGENT},
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except (httpx.HTTPError, ValueError):
        return None
    finally:
        if owned:
            c.close()


def _title_candidates(geo: dict, query: str) -> list[str]:
    """Reasonable Wikipedia titles to try, most specific first."""
    addr = geo.get("address", {}) if geo else {}
    name = (geo or {}).get("name") or query.split(",")[0].strip()
    district = addr.get("state_district") or addr.get("county")
    cands = [name]
    if district and district != name:
        cands.append(f"{name}, {district}")
    cands.append(query.split(",")[0].strip())
    # De-dupe, keep order.
    seen: set[str] = set()
    return [c for c in cands if c and not (c in seen or seen.add(c))]


def lookup_place(query: str, client: httpx.Client | None = None) -> PlaceFacts:
    """Main entry: build PlaceFacts for a place name. Raises PlaceNotFound."""
    query = " ".join(query.split())
    if not query:
        raise PlaceNotFound("empty query")

    geo = geocode(query, client)
    if geo is None:
        raise PlaceNotFound(f"no trusted source recognised {query!r}")

    addr = geo.get("address", {})
    facts = PlaceFacts(
        query=query,
        name=geo.get("name") or query.split(",")[0].strip(),
        lat=float(geo["lat"]) if geo.get("lat") else None,
        lon=float(geo["lon"]) if geo.get("lon") else None,
        place_type=geo.get("type") or geo.get("addresstype"),
        district=addr.get("state_district") or addr.get("county"),
        state=addr.get("state"),
        country=addr.get("country"),
        sources=["nominatim"],
    )

    for title in _title_candidates(geo, query):
        summary = wiki_summary(title, client)
        # Only accept a real place article (not a disambiguation / person / etc.).
        if summary and summary.get("type") == "standard" and summary.get("extract"):
            facts.summary = summary["extract"]
            facts.wikipedia_title = summary.get("title")
            facts.sources.append("wikipedia")
            break

    return facts
