"""Tests for the opt-in self-analysis endpoint (Step 24)."""

STUDENT_POSTS = {
    "consent": True,
    "posts": ["exam tomorrow and assignment due", "hostel fest was fun",
              "backlog cleared this semester", "viva went okay"],
    "post_hours": [1, 23, 2, 0],
    "hashtags": ["#studentlife", "#exams"],
}


def test_requires_login(client):
    assert client.post("/me/analyze", json=STUDENT_POSTS).status_code == 401


def test_requires_consent(client, make_user):
    _, h = make_user()
    body = {**STUDENT_POSTS, "consent": False}
    assert client.post("/me/analyze", json=body, headers=h).status_code == 422


def test_requires_posts(client, make_user):
    _, h = make_user()
    assert client.post("/me/analyze", json={"consent": True, "posts": []}, headers=h).status_code == 422


def test_returns_occupation_and_interests(client, make_user):
    _, h = make_user()
    body = client.post("/me/analyze", json=STUDENT_POSTS, headers=h).json()
    occ = body["occupation"]
    assert occ["label"] == "student"
    assert abs(sum(occ["probabilities"].values()) - 1.0) < 0.01  # rounded to 3dp
    assert occ["reasons"]
    assert "exam" in body["suggested_interests"] or "hostel" in body["suggested_interests"]
    assert "stored" in body["note"].lower()


def test_probabilities_cover_all_classes(client, make_user):
    _, h = make_user()
    occ = client.post("/me/analyze", json=STUDENT_POSTS, headers=h).json()["occupation"]
    assert set(occ["probabilities"]) == {"student", "teacher", "researcher", "industry", "other"}


def test_nothing_stored_about_posts(client, make_user):
    # The user row must not gain the posts; /me should be unchanged.
    uid, h = make_user("Asha", ["ai"])
    client.post("/me/analyze", json=STUDENT_POSTS, headers=h)
    me = client.get("/me", headers=h).json()
    assert me == {"id": uid, "display_name": "Asha", "interests": ["ai"]}
