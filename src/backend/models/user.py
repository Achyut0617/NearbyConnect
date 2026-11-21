from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime | None) -> datetime | None:
    """SQLite gives back datetimes without a timezone; treat them as UTC."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


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

    # --- Location sharing (Step 8) ---
    # Only the LAST location is kept (no history), and only while sharing is on.
    share_location: Mapped[bool] = mapped_column(Boolean, default=False)
    last_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)

    # --- Push notifications (Step 14) ---
    # Expo push token like "ExponentPushToken[xxxx]". Only set if the user allowed notifications.
    push_token: Mapped[str | None] = mapped_column(String(200), nullable=True)

    def clear_location(self) -> None:
        self.share_location = False
        self.last_lat = None
        self.last_lon = None
        self.location_updated_at = None
