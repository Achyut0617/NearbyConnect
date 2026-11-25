"""Backup places provider: Geoapify Places API (step 26).

Geoapify serves the same OpenStreetMap data as Overpass, but from paid,
reliable servers with a free tier (needs a free key: GEOAPIFY_API_KEY).
We only use it when every Overpass server has failed.

Results are converted to the SAME shape osm_client returns, so the rest
of the app (clean, score, rank) does not care where places came from:
    {"osm_id", "name", "type_key", "type", "lat", "lon"}

Privacy: like osm_client, we never log the coordinates we are asked about.
"""

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
