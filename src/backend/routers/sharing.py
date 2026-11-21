"""Location sharing with other NearbyConnect users (Step 8).

Rules:
- Stored ONLY when the user sends consent=true.
- consent=false (or DELETE) erases the stored location right away.
- Only the last location is kept: each update overwrites the previous one.
- Locations older than LOCATION_MAX_AGE are treated as stale (not used for matching).
- Coordinates are never logged and never shown to other users.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from auth import get_current_user
from db import get_db
from models.user import User, as_utc, utcnow

router = APIRouter()

LOCATION_MAX_AGE = timedelta(hours=2)


class LocationUpdate(BaseModel):
    consent: bool
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)

    @model_validator(mode="after")
    def coords_needed_when_sharing(self):
        if self.consent and (self.lat is None or self.lon is None):
            raise ValueError("lat and lon are required when consent is true")
        return self


def is_fresh(user: User) -> bool:
    """True if the user is sharing and their location is recent enough to use."""
    updated = as_utc(user.location_updated_at)
    return (
        user.share_location
        and user.last_lat is not None
        and user.last_lon is not None
        and updated is not None
        and utcnow() - updated <= LOCATION_MAX_AGE
    )


def _status(user: User) -> dict:
    updated = as_utc(user.location_updated_at)
    return {
        "sharing": bool(user.share_location),
        "updated_at": updated.isoformat() if updated else None,
        "fresh": is_fresh(user),
    }


@router.put("/me/location")
def update_location(body: LocationUpdate, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if body.consent:
        user.share_location = True
        user.last_lat = body.lat
        user.last_lon = body.lon
        user.location_updated_at = utcnow()
    else:
        # No consent: erase anything stored, ignore any coordinates sent.
        user.clear_location()
    db.add(user)
    db.commit()
    return _status(user)


@router.get("/me/location")
def location_status(user: User = Depends(get_current_user)):
    """Whether you're sharing. (Coordinates are not echoed back.)"""
    return _status(user)


@router.delete("/me/location")
def stop_sharing(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.clear_location()
    db.add(user)
    db.commit()
    return _status(user)
