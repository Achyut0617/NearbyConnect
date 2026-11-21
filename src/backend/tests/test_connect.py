"""Tests for connect requests (Step 10)."""


def send(client, headers, to_id):
    return client.post("/connect-requests", json={"to_user_id": to_id}, headers=headers)


def test_request_is_pending_until_approved(client, make_user):
    # The Step 10 "Check" from PLAN.md.
    alice_id, alice = make_user("Alice", ["ai"])
    bob_id, bob = make_user("Bob", ["ai"])

    r = send(client, alice, bob_id)
    assert r.status_code == 201
    req = r.json()
    assert req["status"] == "pending"
    assert req["from_user"]["id"] == alice_id and req["to_user"]["id"] == bob_id

    # Not connected yet, for either side.
    assert client.get("/connections", headers=alice).json()["connections"] == []
    assert client.get("/connections", headers=bob).json()["connections"] == []

    # Shows up as pending for both.
    assert client.get("/connect-requests", headers=bob).json()["incoming"][0]["status"] == "pending"
    assert client.get("/connect-requests", headers=alice).json()["outgoing"][0]["status"] == "pending"

    # Bob approves -> now connected.
    r = client.post(f"/connect-requests/{req['id']}/accept", headers=bob)
    assert r.status_code == 200 and r.json()["status"] == "accepted"
    assert client.get("/connections", headers=alice).json()["connections"][0]["display_name"] == "Bob"
    assert client.get("/connections", headers=bob).json()["connections"][0]["display_name"] == "Alice"
    # And no longer listed as pending.
    assert client.get("/connect-requests", headers=bob).json()["incoming"] == []


def test_sender_cannot_accept_own_request(client, make_user):
    _, alice = make_user("Alice")
    bob_id, _ = make_user("Bob")
    req_id = send(client, alice, bob_id).json()["id"]
    assert client.post(f"/connect-requests/{req_id}/accept", headers=alice).status_code == 403


def test_outsider_cannot_see_or_answer_request(client, make_user):
    _, alice = make_user("Alice")
    bob_id, _ = make_user("Bob")
    _, eve = make_user("Eve")
    req_id = send(client, alice, bob_id).json()["id"]
    assert client.post(f"/connect-requests/{req_id}/accept", headers=eve).status_code == 404
    assert client.get("/connect-requests", headers=eve).json() == {"incoming": [], "outgoing": []}


def test_decline(client, make_user):
    _, alice = make_user("Alice")
    bob_id, bob = make_user("Bob")
    req_id = send(client, alice, bob_id).json()["id"]
    r = client.post(f"/connect-requests/{req_id}/decline", headers=bob)
    assert r.json()["status"] == "declined"
    assert client.get("/connections", headers=alice).json()["connections"] == []


def test_cannot_resend_after_decline(client, make_user):
    _, alice = make_user("Alice")
    bob_id, bob = make_user("Bob")
    req_id = send(client, alice, bob_id).json()["id"]
    client.post(f"/connect-requests/{req_id}/decline", headers=bob)
    assert send(client, alice, bob_id).status_code == 409


def test_declined_person_can_still_reach_out_later(client, make_user):
    # Bob said no to Alice; Bob may still change his mind and ask Alice.
    alice_id, alice = make_user("Alice")
    bob_id, bob = make_user("Bob")
    req_id = send(client, alice, bob_id).json()["id"]
    client.post(f"/connect-requests/{req_id}/decline", headers=bob)
    assert send(client, bob, alice_id).status_code == 201


def test_cannot_answer_twice(client, make_user):
    _, alice = make_user("Alice")
    bob_id, bob = make_user("Bob")
    req_id = send(client, alice, bob_id).json()["id"]
    client.post(f"/connect-requests/{req_id}/accept", headers=bob)
    assert client.post(f"/connect-requests/{req_id}/decline", headers=bob).status_code == 409


def test_no_duplicate_pending_either_direction(client, make_user):
    alice_id, alice = make_user("Alice")
    bob_id, bob = make_user("Bob")
    send(client, alice, bob_id)
    assert send(client, alice, bob_id).status_code == 409
    assert send(client, bob, alice_id).status_code == 409


def test_no_request_when_already_connected(client, make_user):
    alice_id, alice = make_user("Alice")
    bob_id, bob = make_user("Bob")
    req_id = send(client, alice, bob_id).json()["id"]
    client.post(f"/connect-requests/{req_id}/accept", headers=bob)
    assert send(client, bob, alice_id).status_code == 409


def test_cannot_connect_with_self_or_unknown(client, make_user):
    me_id, me = make_user("Me")
    assert send(client, me, me_id).status_code == 400
    assert send(client, me, 99999).status_code == 404


def test_unknown_request_id(client, make_user):
    _, me = make_user("Me")
    assert client.post("/connect-requests/12345/accept", headers=me).status_code == 404


def test_requires_login(client):
    assert client.post("/connect-requests", json={"to_user_id": 1}).status_code == 401
    assert client.get("/connections").status_code == 401
