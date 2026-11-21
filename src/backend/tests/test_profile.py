"""Tests for sign-up and interests (Step 5)."""

from sqlalchemy import select

from db import SessionLocal
from models.user import User


def test_signup_returns_id_and_token(client):
    r = client.post("/users", json={"display_name": "  Achyut  "})
    assert r.status_code == 201
    body = r.json()
    assert body["display_name"] == "Achyut"
    assert len(body["token"]) > 20


def test_signup_blank_name_rejected(client):
    assert client.post("/users", json={"display_name": "   "}).status_code == 422
    assert client.post("/users", json={}).status_code == 422


def test_token_is_stored_hashed_not_plain(client):
    token = client.post("/users", json={"display_name": "A"}).json()["token"]
    with SessionLocal() as db:
        user = db.scalar(select(User))
        assert user.token_hash != token
        assert len(user.token_hash) == 64


def test_post_then_get_returns_same_tags(client, make_user):
    # The Step 5 "Check" from PLAN.md.
    _, headers = make_user()
    r = client.put("/me/interests", json={"interests": ["AI", "startups"]}, headers=headers)
    assert r.status_code == 200
    r = client.get("/me/interests", headers=headers)
    assert r.json() == {"interests": ["ai", "startups"]}


def test_interests_are_cleaned(client, make_user):
    _, headers = make_user()
    r = client.put("/me/interests",
                   json={"interests": ["  AI ", "ai", "", "Machine   Learning", "   "]},
                   headers=headers)
    assert r.json()["interests"] == ["ai", "machine learning"]


def test_interests_replace_not_append(client, make_user):
    _, headers = make_user(interests=["ai"])
    client.put("/me/interests", json={"interests": ["music"]}, headers=headers)
    assert client.get("/me/interests", headers=headers).json()["interests"] == ["music"]


def test_too_many_or_too_long_interests_rejected(client, make_user):
    _, headers = make_user()
    many = [f"tag{i}" for i in range(21)]
    assert client.put("/me/interests", json={"interests": many}, headers=headers).status_code == 422
    assert client.put("/me/interests", json={"interests": ["x" * 41]}, headers=headers).status_code == 422


def test_requires_token(client):
    assert client.get("/me/interests").status_code == 401
    assert client.get("/me/interests", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.put("/me/interests", json={"interests": ["ai"]}).status_code == 401


def test_users_cannot_see_each_others_interests(client, make_user):
    _, alice = make_user("Alice", ["ai"])
    _, bob = make_user("Bob", ["music"])
    assert client.get("/me/interests", headers=alice).json()["interests"] == ["ai"]
    assert client.get("/me/interests", headers=bob).json()["interests"] == ["music"]


def test_get_me(client, make_user):
    uid, headers = make_user("Alice", ["ai"])
    assert client.get("/me", headers=headers).json() == {
        "id": uid, "display_name": "Alice", "interests": ["ai"]}
