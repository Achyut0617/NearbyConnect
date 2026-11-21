"""Tests for push notifications (Step 14). The Expo service is faked in conftest."""

import pytest

from db import SessionLocal
from models.user import User

GOOD_TOKEN = "ExponentPushToken[abc123XYZ]"


def set_token(client, headers, token=GOOD_TOKEN):
    return client.put("/me/push-token", json={"token": token}, headers=headers)


def stored_token(user_id):
    with SessionLocal() as db:
        return db.get(User, user_id).push_token


# ---------- saving the token ----------

def test_save_and_delete_push_token(client, make_user):
    uid, h = make_user()
    assert set_token(client, h).json() == {"notifications": True}
    assert stored_token(uid) == GOOD_TOKEN
    assert client.delete("/me/push-token", headers=h).json() == {"notifications": False}
    assert stored_token(uid) is None


@pytest.mark.parametrize("bad", ["", "hello", "ExponentPushToken[]", "https://evil.example"])
def test_rejects_bad_tokens(client, make_user, bad):
    _, h = make_user()
    assert set_token(client, h, bad).status_code == 422


def test_new_style_token_name_accepted(client, make_user):
    _, h = make_user()
    assert set_token(client, h, "ExpoPushToken[abc]").status_code == 200


def test_push_token_requires_login(client):
    assert client.put("/me/push-token", json={"token": GOOD_TOKEN}).status_code == 401


# ---------- notifications on connect events ----------

def test_recipient_notified_of_new_request(client, make_user, sent_pushes):
    _, alice = make_user("Alice")
    bob_id, bob = make_user("Bob")
    set_token(client, bob)
    client.post("/connect-requests", json={"to_user_id": bob_id}, headers=alice)
    assert len(sent_pushes) == 1
    msg = sent_pushes[0]
    assert msg["to"] == GOOD_TOKEN
    assert msg["title"] == "New connect request"
    assert "Alice" in msg["body"]
    assert msg["data"] == {"screen": "requests"}


def test_sender_notified_when_accepted(client, make_user, sent_pushes):
    _, alice = make_user("Alice")
    bob_id, bob = make_user("Bob")
    set_token(client, alice, "ExponentPushToken[alice]")
    req_id = client.post("/connect-requests", json={"to_user_id": bob_id}, headers=alice).json()["id"]
    assert sent_pushes == []                                   # Bob has no token: nothing sent
    client.post(f"/connect-requests/{req_id}/accept", headers=bob)
    assert len(sent_pushes) == 1
    assert sent_pushes[0]["to"] == "ExponentPushToken[alice]"
    assert "Bob accepted" in sent_pushes[0]["body"]


def test_no_notification_on_decline(client, make_user, sent_pushes):
    _, alice = make_user("Alice")
    bob_id, bob = make_user("Bob")
    set_token(client, alice, "ExponentPushToken[alice]")
    req_id = client.post("/connect-requests", json={"to_user_id": bob_id}, headers=alice).json()["id"]
    client.post(f"/connect-requests/{req_id}/decline", headers=bob)
    assert sent_pushes == []   # we don't tell people they were declined


def test_push_failure_does_not_break_request(client, make_user, monkeypatch):
    def broken(message):
        raise ConnectionError("Expo is down")

    monkeypatch.setattr("services.push.send_to_expo", broken)
    _, alice = make_user("Alice")
    bob_id, bob = make_user("Bob")
    set_token(client, bob)
    r = client.post("/connect-requests", json={"to_user_id": bob_id}, headers=alice)
    assert r.status_code == 201 and r.json()["status"] == "pending"


def test_dead_token_is_forgotten(client, make_user, monkeypatch):
    monkeypatch.setattr("services.push.send_to_expo", lambda m: {
        "data": {"status": "error", "message": "gone",
                 "details": {"error": "DeviceNotRegistered"}}})
    _, alice = make_user("Alice")
    bob_id, bob = make_user("Bob")
    set_token(client, bob)
    client.post("/connect-requests", json={"to_user_id": bob_id}, headers=alice)
    assert stored_token(bob_id) is None


def test_push_never_contains_location(client, make_user, sent_pushes):
    _, alice = make_user("Alice", ["ai"])
    bob_id, bob = make_user("Bob", ["ai"])
    client.put("/me/location", json={"consent": True, "lat": 18.5234, "lon": 73.8567}, headers=alice)
    set_token(client, bob)
    client.post("/connect-requests", json={"to_user_id": bob_id}, headers=alice)
    text = str(sent_pushes)
    assert "18.5234" not in text and "73.8567" not in text
