"""Tests for nearby opted-in users (Step 9)."""

from datetime import timedelta

from db import SessionLocal
from models.user import User, utcnow
from services.matching import rough_distance

HOME = (18.5200, 73.8500)
CLOSE = (18.5230, 73.8500)    # ~330 m away
FAR = (18.6200, 73.8500)      # ~11 km away


def share(client, headers, where):
    r = client.put("/me/location",
                   json={"consent": True, "lat": where[0], "lon": where[1]}, headers=headers)
    assert r.status_code == 200


def nearby(client, headers, **params):
    return client.get("/me/nearby-users", headers=headers, params=params)


def test_shared_interest_and_close_matches(client, make_user):
    # The Step 9 "Check" from PLAN.md, part 1.
    _, me = make_user("Me", ["ai", "startups"])
    bob_id, bob = make_user("Bob", ["startups", "music"])
    share(client, me, HOME)
    share(client, bob, CLOSE)
    body = nearby(client, me).json()
    assert body["count"] == 1
    match = body["users"][0]
    assert match == {"user_id": bob_id, "display_name": "Bob",
                     "shared_interests": ["startups"], "approx_distance_m": 400}


def test_far_away_user_does_not_match(client, make_user):
    # Part 2: too far.
    _, me = make_user("Me", ["ai"])
    _, far = make_user("Far", ["ai"])
    share(client, me, HOME)
    share(client, far, FAR)
    assert nearby(client, me).json()["users"] == []


def test_no_overlap_user_does_not_match(client, make_user):
    # Part 3: close but nothing in common.
    _, me = make_user("Me", ["ai"])
    _, other = make_user("Other", ["gardening"])
    share(client, me, HOME)
    share(client, other, CLOSE)
    assert nearby(client, me).json()["users"] == []


def test_non_sharing_user_never_appears(client, make_user):
    _, me = make_user("Me", ["ai"])
    _, hidden = make_user("Hidden", ["ai"])
    share(client, me, HOME)
    share(client, hidden, CLOSE)
    client.delete("/me/location", headers=hidden)      # turned sharing off
    assert nearby(client, me).json()["users"] == []


def test_stale_location_does_not_match(client, make_user):
    _, me = make_user("Me", ["ai"])
    old_id, old = make_user("Old", ["ai"])
    share(client, me, HOME)
    share(client, old, CLOSE)
    with SessionLocal() as db:                          # pretend it was 3 hours ago
        u = db.get(User, old_id)
        u.location_updated_at = utcnow() - timedelta(hours=3)
        db.commit()
    assert nearby(client, me).json()["users"] == []


def test_must_share_to_see_others(client, make_user):
    _, me = make_user("Me", ["ai"])
    _, bob = make_user("Bob", ["ai"])
    share(client, bob, CLOSE)
    r = nearby(client, me)                              # me is NOT sharing
    assert r.status_code == 409


def test_never_returns_coordinates(client, make_user):
    _, me = make_user("Me", ["ai"])
    _, bob = make_user("Bob", ["ai"])
    share(client, me, HOME)
    share(client, bob, CLOSE)
    text = nearby(client, me).text
    assert "18.523" not in text and "lat" not in text and "lon" not in text


def test_does_not_include_myself(client, make_user):
    _, me = make_user("Me", ["ai"])
    share(client, me, HOME)
    assert nearby(client, me).json()["users"] == []


def test_sorted_by_shared_interests_then_distance(client, make_user):
    _, me = make_user("Me", ["ai", "startups", "music"])
    _, one = make_user("OneShared", ["ai"])
    _, two = make_user("TwoShared", ["ai", "music"])
    _, one_closer = make_user("OneCloser", ["startups"])
    share(client, me, HOME)
    share(client, one, (18.5240, 73.85))
    share(client, two, (18.5280, 73.85))
    share(client, one_closer, (18.5210, 73.85))
    names = [u["display_name"] for u in nearby(client, me).json()["users"]]
    assert names == ["TwoShared", "OneCloser", "OneShared"]


def test_radius_param(client, make_user):
    _, me = make_user("Me", ["ai"])
    _, bob = make_user("Bob", ["ai"])
    share(client, me, HOME)
    share(client, bob, CLOSE)                           # ~330 m
    assert nearby(client, me, radius_m=200).json()["users"] == []
    assert nearby(client, me, radius_m=500).json()["count"] == 1
    assert nearby(client, me, radius_m=99999).status_code == 422


def test_requires_login(client):
    assert client.get("/me/nearby-users").status_code == 401


def test_rough_distance():
    assert rough_distance(0) == 100
    assert rough_distance(12) == 100
    assert rough_distance(100) == 100
    assert rough_distance(101) == 200
    assert rough_distance(340) == 400
