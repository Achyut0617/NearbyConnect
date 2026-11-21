"""Clean the raw place list from osm_client.fetch_places().

Steps, in order:
1. Drop entries with no usable name or bad coordinates.
2. Tidy names (trim and collapse extra spaces).
3. Remove duplicates (same OSM id, or same name within DUPLICATE_DISTANCE_M).
4. Add a simple "category" from a small fixed set, so scoring is easy later.
"""

import math

# If two places have the same name and are closer than this, treat them as one.
# (OSM sometimes maps the same cafe as a point AND as a building outline.)
DUPLICATE_DISTANCE_M = 50

# The small, fixed set of categories the rest of the app uses.
CATEGORIES = (
    "food", "cafe", "coworking", "education", "event_space",
    "culture", "outdoors", "fitness", "shopping", "office", "other",
)

# Exact OSM tag -> our category. Checked first.
TAG_TO_CATEGORY = {
    ("amenity", "restaurant"): "food",
    ("amenity", "fast_food"): "food",
    ("amenity", "food_court"): "food",
    ("amenity", "bar"): "food",
    ("amenity", "pub"): "food",
    ("amenity", "cafe"): "cafe",
    ("shop", "coffee"): "cafe",
    ("amenity", "coworking_space"): "coworking",
    ("office", "coworking"): "coworking",
    ("amenity", "library"): "education",
    ("amenity", "university"): "education",
    ("amenity", "college"): "education",
    ("amenity", "school"): "education",
    ("amenity", "community_centre"): "event_space",
    ("amenity", "conference_centre"): "event_space",
    ("amenity", "events_venue"): "event_space",
    ("amenity", "arts_centre"): "event_space",
    ("amenity", "theatre"): "culture",
    ("tourism", "museum"): "culture",
    ("tourism", "gallery"): "culture",
    ("tourism", "attraction"): "culture",
    ("leisure", "park"): "outdoors",
    ("leisure", "garden"): "outdoors",
    ("leisure", "fitness_centre"): "fitness",
    ("leisure", "sports_centre"): "fitness",
}

# If no exact match: fall back on the tag key alone.
# e.g. any shop=* that isn't coffee -> "shopping"; any office=* -> "office".
KEY_TO_CATEGORY = {
    "shop": "shopping",
    "office": "office",
}


def categorize(type_key: str | None, type_value: str | None) -> str:
    """Map an OSM tag like ("amenity", "cafe") to one of CATEGORIES."""
    key = (type_key or "").strip().lower()
    value = (type_value or "").strip().lower()
    if (key, value) in TAG_TO_CATEGORY:
        return TAG_TO_CATEGORY[(key, value)]
    return KEY_TO_CATEGORY.get(key, "other")


def clean_name(name) -> str:
    """Trim and collapse whitespace. Returns "" if there's no real name."""
    if not isinstance(name, str):
        return ""
    return " ".join(name.split())


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance in metres between two GPS points (haversine formula)."""
    r = 6_371_000  # Earth's radius in metres
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _valid_coords(place: dict) -> bool:
    lat, lon = place.get("lat"), place.get("lon")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return False
    return -90 <= lat <= 90 and -180 <= lon <= 180


def clean_places(raw: list[dict]) -> list[dict]:
    """Return a cleaned, de-duplicated, categorised copy of `raw`.

    The original list is not changed. The first copy of a duplicate is kept.
    """
    kept: list[dict] = []
    seen_ids: set[str] = set()

    for place in raw:
        name = clean_name(place.get("name"))
        if not name or not _valid_coords(place):
            continue

        osm_id = place.get("osm_id")
        if osm_id and osm_id in seen_ids:
            continue

        # Same name (ignoring case) and very close -> duplicate.
        is_dup = any(
            k["name"].lower() == name.lower()
            and distance_m(k["lat"], k["lon"], place["lat"], place["lon"]) < DUPLICATE_DISTANCE_M
            for k in kept
        )
        if is_dup:
            continue

        if osm_id:
            seen_ids.add(osm_id)
        kept.append({
            **place,
            "name": name,
            "category": categorize(place.get("type_key"), place.get("type")),
        })

    return kept
