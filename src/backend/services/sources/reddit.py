"""Stage B source: Reddit public search (official API).

Reads PUBLIC posts matching a keyword. Needs a free Reddit "script" app:
set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env (see docs/API_KEYS.md).
Without them, raises SourceUnavailable (callers treat that as "skip this source").

We request only what we need and never write anything to Reddit.
"""

from __future__ import annotations

import os

import httpx

from services.sources.base import Post, SourceUnavailable, extract_hashtags, hash_author

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
SEARCH_URL = "https://oauth.reddit.com/search"
USER_AGENT = "NearbyConnect/0.1 (educational project)"
TIMEOUT = 15


def _credentials() -> tuple[str, str]:
    cid = os.getenv("REDDIT_CLIENT_ID")
    secret = os.getenv("REDDIT_CLIENT_SECRET")
    if not cid or not secret:
        raise SourceUnavailable("Reddit API keys not set (REDDIT_CLIENT_ID/SECRET)")
    return cid, secret


def _get_token(client: httpx.Client) -> str:
    cid, secret = _credentials()
    resp = client.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(cid, secret),
        headers={"User-Agent": USER_AGENT},
    )
    if resp.status_code != 200:
        raise SourceUnavailable(f"Reddit auth failed (HTTP {resp.status_code})")
    return resp.json()["access_token"]


def search(keyword: str, limit: int = 50, client: httpx.Client | None = None) -> list[Post]:
    """Return public Reddit posts matching `keyword`. Raises SourceUnavailable."""
    own = client is None
    if own:
        client = httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
    try:
        token = _get_token(client)
        resp = client.get(
            SEARCH_URL,
            params={"q": keyword, "limit": min(limit, 100), "sort": "new", "type": "link"},
            headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT},
        )
        if resp.status_code != 200:
            raise SourceUnavailable(f"Reddit search failed (HTTP {resp.status_code})")
        return parse(resp.json())
    except httpx.HTTPError as e:
        raise SourceUnavailable(f"Reddit network error: {type(e).__name__}") from e
    finally:
        if own:
            client.close()


def parse(data: dict) -> list[Post]:
    """Turn Reddit's listing JSON into Post objects."""
    posts: list[Post] = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        text = f"{d.get('title', '')} {d.get('selftext', '')}".strip()
        if not text:
            continue
        posts.append(Post(
            source="reddit",
            text=text,
            author_ref=hash_author("reddit", d.get("author", "") or "unknown"),
            hashtags=extract_hashtags(text),
            created_utc=d.get("created_utc"),
        ))
    return posts
