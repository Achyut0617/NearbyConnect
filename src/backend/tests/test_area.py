"""Tests for the /area-intel and /area-trends endpoints (Step 19).

Place lookup and the sources are patched so everything runs offline.
"""

import pytest

import routers.area as area
from services.place_intel import PlaceFacts, PlaceNotFound
from services.sources.base import Post, SourceUnavailable, hash_author

FACTS = PlaceFacts(
    query="Loni Kalbhor, Pune", name="Loni Kalbhor", district="Pune",
    state="Maharashtra", summary="Loni Kalbhor is known for engineering colleges.",
)


@pytest.fixture
def patch_lookup(monkeypatch):
    monkeypatch.setattr(area, "lookup_place", lambda place, client=None: FACTS)


def test_area_intel_requires_login(client):
    assert client.get("/area-intel", params={"place": "Pune"}).status_code == 401


def test_area_intel_returns_facts_and_terms(client, make_user, patch_lookup):
    _, h = make_user()
    r = client.get("/area-intel", params={"place": "Loni Kalbhor, Pune"}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["facts"]["name"] == "Loni Kalbhor"
    assert "Loni Kalbhor" in body["terms"]["keywords"]


def test_area_intel_404_for_unknown(client, make_user, monkeypatch):
    _, h = make_user()
    def boom(place, client=None):
        raise PlaceNotFound(place)
    monkeypatch.setattr(area, "lookup_place", boom)
    assert client.get("/area-intel", params={"place": "zzz"}, headers=h).status_code == 404


def test_area_trends_aggregates_and_hides_identities(client, make_user, patch_lookup, monkeypatch):
    _, h = make_user()
    # 25 distinct authors all mention "cricket".
    posts = [Post("reddit", "love cricket", hash_author("reddit", f"u{i}")) for i in range(25)]
    monkeypatch.setattr(area.reddit, "search", lambda term, limit=50: posts)
    monkeypatch.setattr(area.youtube, "search",
                        lambda term, limit=50: (_ for _ in ()).throw(SourceUnavailable("no key")))

    body = client.get("/area-trends", params={"place": "Loni Kalbhor"}, headers=h).json()
    assert body["trends"]["sources_used"] == ["reddit"]
    assert any(t["term"] == "cricket" for t in body["trends"]["topics"])
    assert body["sources_skipped"]["youtube"]
    # No author ref should appear anywhere.
    refs = {p.author_ref for p in posts}
    assert not any(ref in str(body) for ref in refs)


def test_area_trends_all_sources_skipped(client, make_user, patch_lookup, monkeypatch):
    _, h = make_user()
    skip = lambda term, limit=50: (_ for _ in ()).throw(SourceUnavailable("no key"))
    monkeypatch.setattr(area.reddit, "search", skip)
    monkeypatch.setattr(area.youtube, "search", skip)
    body = client.get("/area-trends", params={"place": "Pune"}, headers=h).json()
    assert body["trends"]["sources_used"] == []
    assert body["trends"]["total_posts"] == 0
    assert set(body["sources_skipped"]) == {"reddit", "youtube"}
