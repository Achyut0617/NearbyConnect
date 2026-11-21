from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """A NearbyConnect user. Only people who signed up themselves exist here."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(50))
    # We store a HASH of the login token, never the token itself.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # e.g. ["ai", "startups"]
    interests: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
