"""Tests for Stage B: sources parsing + aggregation with k-author threshold."""

import httpx
import pytest

from services.sources import reddit, youtube
from services.sources.base import Post, SourceUnavailable, extract_hashtags, hash_author
from services.trends import aggregate, contains_identity


# ---------- source parsing (offline) ----------

def test_reddit_parse():
    data = {"data": {"children": [
        {"data": {"title": "Pune food scene", "selftext": "love #punefoodie", "author": "u1",
                  "created_utc": 1.0}},
        {"data": {"title": "", "selftext": "", "author": "u2"}},  # empty -> skipped
    ]}}
    posts = reddit.parse(data)
    assert len(posts) == 1
    assert posts[0].source == "reddit" and "#punefoodie" in posts[0].hashtags


def test_youtube_parse():
    data = {"items": [
        {"snippet": {"title": "Loni Kalbhor vlog", "description": "#pune college fest",
                     "channelId": "c1"}},
    ]}
    posts = youtube.parse(data)
    assert posts[0].source == "youtube" and "#pune" in posts[0].hashtags


def test_reddit_unavailable_without_keys(monkeypatch):
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    with pytest.raises(SourceUnavailable):
        reddit.search("pune", client=httpx.Client(transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={}))))


def test_youtube_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    with pytest.raises(SourceUnavailable):
        youtube.search("pune", client=httpx.Client(transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={}))))


def test_extract_hashtags():
    assert extract_hashtags("fun at #Pune with #LoniKalbhor!") == ["#pune", "#lonikalbhor"]


# ---------- aggregation + privacy threshold ----------

def make_posts(term_authors: dict[str, int], source="reddit"):
    """Build posts where `term` was used by N distinct authors."""
    posts = []
    n = 0
    for term, authors in term_authors.items():
        for _ in range(authors):
            n += 1
            posts.append(Post(source=source, text=f"I love {term} today",
                              author_ref=hash_author(source, f"user{n}")))
    return posts


def test_topic_below_threshold_is_dropped():
    posts = make_posts({"cricket": 25, "obscure": 5})
    out = aggregate("Pune", posts, ["reddit"], min_authors=20)
    terms = [t.term for t in out.topics]
    assert "cricket" in terms
    assert "obscure" not in terms            # only 5 authors -> dropped


def test_same_author_repeating_does_not_pass_threshold():
    # One author posting 30 times must NOT make a topic appear.
    posts = [Post("reddit", "spam cricket cricket", hash_author("reddit", "same")) for _ in range(30)]
    out = aggregate("Pune", posts, ["reddit"], min_authors=20)
    assert out.topics == []                  # distinct authors = 1


def test_output_contains_no_author_refs():
    posts = make_posts({"cricket": 25})
    refs = {p.author_ref for p in posts}
    out = aggregate("Pune", posts, ["reddit"], min_authors=20).to_dict()
    assert not contains_identity(out, refs)  # privacy: no identities leak


def test_hashtags_thresholded():
    posts = [Post("reddit", "x", hash_author("reddit", f"u{i}"), hashtags=["#pune"])
             for i in range(22)]
    posts += [Post("reddit", "y", hash_author("reddit", f"v{i}"), hashtags=["#rare"])
              for i in range(3)]
    out = aggregate("Pune", posts, ["reddit"], min_authors=20)
    tags = [t.term for t in out.hashtags]
    assert "#pune" in tags and "#rare" not in tags


def test_note_when_nothing_passes():
    out = aggregate("Pune", make_posts({"x": 3}), ["reddit"], min_authors=20)
    assert "privacy" in out.note.lower()


def test_sentiment_mood():
    pos = [Post("reddit", "great amazing love", hash_author("reddit", f"u{i}")) for i in range(5)]
    out = aggregate("Pune", pos, ["reddit"], min_authors=1)
    assert out.sentiment["mood"] == "mostly positive"
