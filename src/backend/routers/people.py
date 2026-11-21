"""Nearby people: ONLY NearbyConnect users who opted in (Step 9)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import get_current_user
from db import get_db
from models.user import User
from routers.sharing import is_fresh
from services.matching import find_matches

router = APIRouter()

MAX_PEOPLE_RADIUS_M = 5000


@router.get("/me/nearby-users")
def nearby_users(radius_m: int = Query(2000, gt=0, le=MAX_PEOPLE_RADIUS_M),
                 me: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    # Fairness + privacy: you can only see others while you are visible too.
    if not is_fresh(me):
        raise HTTPException(
            status_code=409,
            detail="Turn on location sharing (with a recent location) to see nearby people.",
        )

    # v1: check every sharing user in Python. Fine for a small app; for many
    # users, move the distance filter into the database (e.g. PostGIS).
    candidates = db.scalars(
        select(User).where(User.share_location.is_(True), User.id != me.id)
    ).all()
    matches = find_matches(me, list(candidates), radius_m)
    return {"radius_m": radius_m, "count": len(matches), "users": matches}
