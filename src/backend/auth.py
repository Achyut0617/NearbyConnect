"""Very simple token login.

On sign-up the server creates a random secret token and gives it to the app
ONCE. The app sends it on every request:  Authorization: Bearer <token>
We only store a SHA-256 hash of it, so a leaked database doesn't leak tokens.
"""

import hashlib
import secrets

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from db import get_db
from models.user import User


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _user_from_header(authorization: str | None, db: Session) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
    return db.scalar(select(User).where(User.token_hash == hash_token(token)))


def get_current_user(authorization: str | None = Header(default=None),
                     db: Session = Depends(get_db)) -> User:
    """Use in an endpoint to REQUIRE a logged-in user (401 otherwise)."""
    user = _user_from_header(authorization, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    return user


def get_optional_user(authorization: str | None = Header(default=None),
                      db: Session = Depends(get_db)) -> User | None:
    """Use in an endpoint where login is optional."""
    return _user_from_header(authorization, db)
