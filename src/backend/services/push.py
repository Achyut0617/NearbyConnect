"""Send push notifications through the Expo Push Service (Step 14).

Docs: https://docs.expo.dev/push-notifications/sending-notifications/
- POST https://exp.host/--/api/v2/push/send with {"to", "title", "body", "data"}
- "status": "ok" only means Expo ACCEPTED it, not that the phone got it.
- "DeviceNotRegistered" means the token is dead (app uninstalled): forget it.

Sending must never break the main request, so every error is caught here.
Privacy: messages never include location data.
"""

import logging
import re

import httpx

from db import SessionLocal
from models.user import User

log = logging.getLogger("nearbyconnect.push")

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
TOKEN_PATTERN = re.compile(r"^Expo(nent)?PushToken\[[^\]]{1,180}\]$")


def is_valid_token(token: str) -> bool:
    return bool(TOKEN_PATTERN.match(token))


def send_to_expo(message: dict) -> dict:
    """Do the real HTTP call. Tests replace this function with a fake."""
    resp = httpx.post(
        EXPO_PUSH_URL,
        json=message,
        headers={"accept": "application/json", "content-type": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def notify_user(user_id: int, title: str, body: str, data: dict | None = None) -> None:
    """Send one notification to a user, if they gave us a push token.

    Runs as a FastAPI background task (after the response was sent), so it
    opens its own database session.
    """
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None or not user.push_token:
            return
        message = {"to": user.push_token, "title": title, "body": body,
                   "data": data or {}, "sound": "default", "channelId": "default"}
        try:
            result = send_to_expo(message)
        except Exception as e:  # network down, Expo error, etc.
            log.warning("push send failed: %s", type(e).__name__)  # no token/user data in logs
            return

        ticket = (result.get("data") or [{}])
        ticket = ticket[0] if isinstance(ticket, list) and ticket else ticket
        if isinstance(ticket, dict) and ticket.get("status") == "error":
            if (ticket.get("details") or {}).get("error") == "DeviceNotRegistered":
                user.push_token = None  # app uninstalled / token expired: stop using it
                db.commit()
            else:
                log.warning("push rejected: %s", (ticket.get("details") or {}).get("error"))
