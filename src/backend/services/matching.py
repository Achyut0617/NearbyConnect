"""Find nearby NearbyConnect users with overlapping interests (Step 9).

Only users who opted in (share_location=True, fresh location) are considered.
Exact coordinates are never returned, only a distance rounded UP to the
next DISTANCE_ROUNDING_M, so nobody can pinpoint another user.
"""

import math

from models.user import User
from routers.sharing import is_fresh
from services.clean import distance_m

DISTANCE_ROUNDING_M = 100


def rough_distance(meters: float) -> int:
    """Round UP to the next 100 m (minimum 100), e.g. 12 -> 100, 340 -> 400."""
    return max(DISTANCE_ROUNDING_M,
               math.ceil(meters / DISTANCE_ROUNDING_M) * DISTANCE_ROUNDING_M)


def find_matches(me: User, candidates: list[User], radius_m: int) -> list[dict]:
    """Return matching users, most shared interests first, then nearest.

    `me` must already be sharing with a fresh location (the router checks).
    """
    my_interests = list(me.interests or [])
    results = []
    for other in candidates:
        if other.id == me.id or not is_fresh(other):
            continue

        theirs = set(other.interests or [])
        shared = [i for i in my_interests if i in theirs]  # keep my order
        if not shared:
            continue

        d = distance_m(me.last_lat, me.last_lon, other.last_lat, other.last_lon)
        if d > radius_m:
            continue

        results.append({
            "user_id": other.id,
            "display_name": other.display_name,
            "shared_interests": shared,
            "approx_distance_m": rough_distance(d),
            "_exact": d,  # only for sorting; removed below
        })

    results.sort(key=lambda r: (-len(r["shared_interests"]), r["_exact"]))
    for r in results:
        del r["_exact"]
    return results
