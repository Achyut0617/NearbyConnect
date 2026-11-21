from fastapi import APIRouter
from pydantic import BaseModel, Field

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


@router.post("/nearby")
def nearby(req: NearbyRequest):
    """Accept a location and confirm it's valid.

    Privacy: we do NOT log or store the coordinates here.
    Place search is added in Step 3, so `places` is empty for now.
    """
    return {
        "lat": req.lat,
        "lon": req.lon,
        "radius_m": req.radius_m,
        "places": [],
    }
