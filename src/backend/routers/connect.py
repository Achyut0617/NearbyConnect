"""Connect requests between NearbyConnect users (Step 10).

A request is only ever created by a user tapping "Connect", and only becomes
a connection when the OTHER user taps "Accept". Nothing is automatic, and
nothing touches any third-party platform.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from auth import get_current_user
from db import get_db
from models.connect_request import ACCEPTED, DECLINED, PENDING, ConnectRequest
from models.user import User, as_utc, utcnow

router = APIRouter()


class ConnectBody(BaseModel):
    to_user_id: int


def _between(a: int, b: int):
    """SQL condition: a request between users a and b, in either direction."""
    return or_(
        and_(ConnectRequest.from_user_id == a, ConnectRequest.to_user_id == b),
        and_(ConnectRequest.from_user_id == b, ConnectRequest.to_user_id == a),
    )


def _out(req: ConnectRequest) -> dict:
    created = as_utc(req.created_at)
    responded = as_utc(req.responded_at)
    return {
        "id": req.id,
        "from_user": {"id": req.from_user.id, "display_name": req.from_user.display_name},
        "to_user": {"id": req.to_user.id, "display_name": req.to_user.display_name},
        "status": req.status,
        "created_at": created.isoformat() if created else None,
        "responded_at": responded.isoformat() if responded else None,
    }


def on_request_created(db: Session, req: ConnectRequest) -> None:
    """Hook called after a request is created (push notifications plug in here)."""


def on_request_accepted(db: Session, req: ConnectRequest) -> None:
    """Hook called after a request is accepted (push notifications plug in here)."""


@router.post("/connect-requests", status_code=201)
def send_request(body: ConnectBody, me: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    if body.to_user_id == me.id:
        raise HTTPException(400, "You can't connect with yourself.")
    if db.get(User, body.to_user_id) is None:
        raise HTTPException(404, "User not found.")

    existing = db.scalars(select(ConnectRequest).where(_between(me.id, body.to_user_id))).all()
    for r in existing:
        if r.status == ACCEPTED:
            raise HTTPException(409, "You're already connected.")
        if r.status == PENDING:
            raise HTTPException(409, "A request between you is already pending.")
        if r.status == DECLINED and r.from_user_id == me.id:
            # Protect people from repeated requests after saying no.
            raise HTTPException(409, "This user declined your earlier request.")

    req = ConnectRequest(from_user_id=me.id, to_user_id=body.to_user_id, status=PENDING)
    db.add(req)
    db.commit()
    db.refresh(req)
    on_request_created(db, req)
    return _out(req)


@router.get("/connect-requests")
def list_requests(me: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Pending requests sent to me (incoming) and by me (outgoing)."""
    incoming = db.scalars(select(ConnectRequest).where(
        ConnectRequest.to_user_id == me.id, ConnectRequest.status == PENDING)
        .order_by(ConnectRequest.created_at.desc())).all()
    outgoing = db.scalars(select(ConnectRequest).where(
        ConnectRequest.from_user_id == me.id, ConnectRequest.status == PENDING)
        .order_by(ConnectRequest.created_at.desc())).all()
    return {"incoming": [_out(r) for r in incoming], "outgoing": [_out(r) for r in outgoing]}


def _respond(request_id: int, new_status: str, me: User, db: Session) -> ConnectRequest:
    req = db.get(ConnectRequest, request_id)
    # Same 404 for "doesn't exist" and "not yours", so ids can't be probed.
    if req is None or me.id not in (req.from_user_id, req.to_user_id):
        raise HTTPException(404, "Request not found.")
    if req.to_user_id != me.id:
        raise HTTPException(403, "Only the person who received the request can answer it.")
    if req.status != PENDING:
        raise HTTPException(409, f"This request was already {req.status}.")
    req.status = new_status
    req.responded_at = utcnow()
    db.commit()
    db.refresh(req)
    return req


@router.post("/connect-requests/{request_id}/accept")
def accept(request_id: int, me: User = Depends(get_current_user), db: Session = Depends(get_db)):
    req = _respond(request_id, ACCEPTED, me, db)
    on_request_accepted(db, req)
    return _out(req)


@router.post("/connect-requests/{request_id}/decline")
def decline(request_id: int, me: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _out(_respond(request_id, DECLINED, me, db))


@router.get("/connections")
def connections(me: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """People I'm connected with (accepted requests in either direction)."""
    reqs = db.scalars(select(ConnectRequest).where(
        ConnectRequest.status == ACCEPTED,
        or_(ConnectRequest.from_user_id == me.id, ConnectRequest.to_user_id == me.id),
    )).all()
    people = []
    for r in reqs:
        other = r.to_user if r.from_user_id == me.id else r.from_user
        since = as_utc(r.responded_at)
        people.append({"user_id": other.id, "display_name": other.display_name,
                       "interests": other.interests,
                       "since": since.isoformat() if since else None})
    return {"connections": people}
