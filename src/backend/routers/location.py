from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from auth import get_optional_user
from models.user import User
from routers.profile import MAX_INTERESTS, normalize_interests
from services.clean import clean_places
from services.osm_client import OverpassUnavailable
from services.place_cache import cached_fetch_places
from services.scoring import rank_places

router = APIRouter()

# Upper limit on search radius, so nobody can ask for "the whole city" at once.
MAX_RADIUS_M = 5000


class NearbyRequest(BaseModel):
    """What the app sends us: where the user is and how far to search.

    Field(...) rules are checked by FastAPI automatically.
    If any rule is broken, FastAPI replies with a 422 error for us.
    """

    lat: float = Field(..., ge=-90, le=90, description="Latitude, -90 to 90")
    lon: float = Field(..., ge=-180, le=180, description="Longitude, -180 to 180")
    radius_m: int = Field(1000, gt=0, le=MAX_RADIUS_M, description="Search radius in metres")
    # Optional. If left out and the user is logged in, their saved interests are used.
    interests: list[str] | None = Field(None, max_length=MAX_INTERESTS)
    limit: int = Field(50, gt=0, le=200, description="Max places to return")

    @field_validator("interests")
    @classmethod
    def clean_interests(cls, v):
        return None if v is None else normalize_interests(v)


def get_place_fetcher():
    """Which function fetches raw places. Tests replace this with a fake.

    Uses the short-lived cache (step 25), so repeat searches are instant.
    """
    return cached_fetch_places


@router.post("/nearby")
def nearby(req: NearbyRequest,
           user: User | None = Depends(get_optional_user),
           fetch=Depends(get_place_fetcher)):
    """Return nearby places ranked by how well they match the user's interests.

    Privacy: we do NOT log or store the coordinates here.
    """
    if req.interests is not None:
        interests = req.interests
    elif user is not None:
        interests = user.interests or []
    else:
        interests = []

    try:
        raw = fetch(req.lat, req.lon, req.radius_m)
    except OverpassUnavailable:
        raise HTTPException(
            status_code=503,
            detail="Place data service is busy right now. Please try again shortly.",
        )

    ranked = rank_places(clean_places(raw), interests, req.lat, req.lon)
    # The cache may search slightly wider than asked; keep only places inside
    # the user's real radius.
    ranked = [p for p in ranked
              if p["distance_m"] is None or p["distance_m"] <= req.radius_m]
    return {
        "radius_m": req.radius_m,
        "interests_used": interests,
        "count": min(len(ranked), req.limit),
        "places": ranked[: req.limit],
    }
