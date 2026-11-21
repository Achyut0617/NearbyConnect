"""Score how relevant a place is to a user's interests (simple keyword version).

Two ways a place earns points:
1. Category match: each known interest "points to" some categories.
   e.g. "startups" -> coworking (3), event_space (2), cafe (1), office (1)
2. Name/type match: an interest word appears in the place's name or OSM type.
   e.g. interest "coffee" and place "Third Wave Coffee" -> +NAME_MATCH_POINTS

Embeddings (smarter "meaning" matching) are deferred until this works well.
"""

import re

from services.clean import distance_m

NAME_MATCH_POINTS = 2

# Groups of interests that point to the same categories.
_TECH = {"coworking": 2, "education": 2, "event_space": 2, "office": 1}
_STARTUP = {"coworking": 3, "event_space": 2, "cafe": 1, "office": 1}
_NETWORK = {"event_space": 3, "coworking": 2, "cafe": 2}
_LEARN = {"education": 3, "cafe": 1}
_CULTURE = {"culture": 3, "event_space": 1}
_FITNESS = {"fitness": 3, "outdoors": 2}
_NATURE = {"outdoors": 3}
_FOOD = {"food": 3, "cafe": 2}
_COFFEE = {"cafe": 3, "food": 1}
_SHOP = {"shopping": 3}

INTEREST_CATEGORIES: dict[str, dict[str, int]] = {
    # startups & business
    "startups": _STARTUP, "entrepreneurship": _STARTUP, "business": _STARTUP,
    "founders": _STARTUP, "freelancing": _STARTUP, "remote work": _STARTUP,
    # tech
    "ai": _TECH, "artificial intelligence": _TECH, "machine learning": _TECH,
    "tech": _TECH, "technology": _TECH, "programming": _TECH, "coding": _TECH,
    "software": _TECH, "data science": _TECH, "web development": _TECH,
    # people
    "networking": _NETWORK, "meetups": _NETWORK, "community": _NETWORK,
    "events": _NETWORK, "public speaking": _NETWORK,
    # learning
    "reading": _LEARN, "books": _LEARN, "learning": _LEARN, "study": _LEARN,
    "studying": _LEARN, "education": _LEARN, "research": _LEARN,
    # culture
    "art": _CULTURE, "design": _CULTURE, "music": _CULTURE, "culture": _CULTURE,
    "history": _CULTURE, "museums": _CULTURE, "photography": _CULTURE,
    "theatre": _CULTURE, "film": _CULTURE,
    # body
    "fitness": _FITNESS, "sports": _FITNESS, "gym": _FITNESS, "yoga": _FITNESS,
    "running": _FITNESS, "cycling": _FITNESS,
    # outdoors
    "nature": _NATURE, "outdoors": _NATURE, "hiking": _NATURE, "walking": _NATURE,
    "parks": _NATURE,
    # food
    "food": _FOOD, "restaurants": _FOOD, "cooking": _FOOD,
    "coffee": _COFFEE, "cafes": _COFFEE, "tea": _COFFEE,
    # shopping
    "shopping": _SHOP, "fashion": _SHOP,
}


def categories_for(interest: str) -> dict[str, int]:
    """Look up an interest, also trying simple singular/plural forms."""
    i = interest.strip().lower()
    for candidate in (i, i + "s", i[:-1] if i.endswith("s") else None):
        if candidate and candidate in INTEREST_CATEGORIES:
            return INTEREST_CATEGORIES[candidate]
    return {}


def _word_in(word: str, text: str) -> bool:
    """True if `word` appears as a whole word in `text` ("ai" not in "Sai")."""
    return re.search(rf"\b{re.escape(word)}s?\b", text, flags=re.IGNORECASE) is not None


def score_place(place: dict, interests: list[str]) -> tuple[int, list[str]]:
    """Return (score, reasons) for one cleaned place."""
    category = place.get("category", "other")
    search_text = f"{place.get('name', '')} {place.get('type', '')}".replace("_", " ")

    score = 0
    reasons: list[str] = []
    for interest in interests:
        points = categories_for(interest).get(category, 0)
        if points:
            score += points
            reasons.append(f"{category.replace('_', ' ')} matches '{interest}'")
        if _word_in(interest, search_text):
            score += NAME_MATCH_POINTS
            reasons.append(f"name mentions '{interest}'")
    return score, reasons


def rank_places(places: list[dict], interests: list[str],
                user_lat: float | None = None, user_lon: float | None = None) -> list[dict]:
    """Add score, reasons and distance to each place; best first.

    Sort order: higher score first, then closer first.
    """
    ranked = []
    for p in places:
        score, reasons = score_place(p, interests)
        dist = None
        if user_lat is not None and user_lon is not None:
            dist = round(distance_m(user_lat, user_lon, p["lat"], p["lon"]))
        ranked.append({**p, "score": score, "reasons": reasons, "distance_m": dist})

    ranked.sort(key=lambda p: (-p["score"],
                               p["distance_m"] if p["distance_m"] is not None else 0))
    return ranked
