"""Sign-up and interest profile endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from auth import get_current_user, hash_token, new_token
from db import get_db
from models.user import User

router = APIRouter()

MAX_INTERESTS = 20
MAX_INTEREST_LEN = 40


def normalize_interests(tags: list[str]) -> list[str]:
    """Trim, lowercase, collapse spaces, drop blanks and repeats (keep order)."""
    out: list[str] = []
    for tag in tags:
        t = " ".join(str(tag).split()).lower()
        if not t:
            continue
        if len(t) > MAX_INTEREST_LEN:
            raise ValueError(f"each interest must be at most {MAX_INTEREST_LEN} characters")
        if t not in out:
            out.append(t)
    return out


class SignupRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=50)

    @field_validator("display_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("display_name cannot be blank")
        return v


class InterestsBody(BaseModel):
    interests: list[str] = Field(..., max_length=MAX_INTERESTS)

    @field_validator("interests")
    @classmethod
    def clean(cls, v: list[str]) -> list[str]:
        return normalize_interests(v)


@router.post("/users", status_code=201)
def sign_up(body: SignupRequest, db: Session = Depends(get_db)):
    """Create a user. The token is returned ONCE: the app must save it."""
    token = new_token()
    user = User(display_name=body.display_name, token_hash=hash_token(token), interests=[])
    db.add(user)
    db.commit()
    return {"id": user.id, "display_name": user.display_name, "token": token}


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {"id": user.id, "display_name": user.display_name, "interests": user.interests}


@router.get("/me/interests")
def get_interests(user: User = Depends(get_current_user)):
    return {"interests": user.interests}


@router.put("/me/interests")
def set_interests(body: InterestsBody, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """Replace the user's interest list with the one sent."""
    user.interests = body.interests
    db.add(user)
    db.commit()
    return {"interests": user.interests}
