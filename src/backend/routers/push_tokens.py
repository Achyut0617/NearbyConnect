"""Save / remove the phone's Expo push token (Step 14)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user
from db import get_db
from models.user import User
from services.push import is_valid_token

router = APIRouter()


class PushTokenBody(BaseModel):
    token: str


@router.put("/me/push-token")
def set_push_token(body: PushTokenBody, me: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    token = body.token.strip()
    if not is_valid_token(token):
        raise HTTPException(422, "That doesn't look like an Expo push token.")
    me.push_token = token
    db.add(me)
    db.commit()
    return {"notifications": True}


@router.delete("/me/push-token")
def delete_push_token(me: User = Depends(get_current_user), db: Session = Depends(get_db)):
    me.push_token = None
    db.add(me)
    db.commit()
    return {"notifications": False}
