from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base
from models.user import User, utcnow

PENDING, ACCEPTED, DECLINED = "pending", "accepted", "declined"


class ConnectRequest(Base):
    """A request from one user to connect with another. Never auto-accepted."""

    __tablename__ = "connect_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(10), default=PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    from_user: Mapped[User] = relationship(foreign_keys=[from_user_id])
    to_user: Mapped[User] = relationship(foreign_keys=[to_user_id])
