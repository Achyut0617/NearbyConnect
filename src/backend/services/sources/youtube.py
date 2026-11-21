"""Stage B source: YouTube Data API v3 search (official API).

Reads PUBLIC videos matching a keyword. Needs a free Google API key:
set YOUTUBE_API_KEY in .env (see docs/API_KEYS.md).
Without it, raises SourceUnavailable (callers skip this source).

channelId is used only as the author reference for distinct-author counting.
"""

from __future__ import annotations

import os

import httpx

from services.sources.base import Post, SourceUnavailable, extract_hashtags, hash_author

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
USER_AGENT = "NearbyConnect/0.1 (educational project)"
TIMEOUT = 15


def _api_key() -> str:
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise SourceUnavailable("YouTube API key not set (YOUTUBE_API_KEY)")
    return key


def search(keyword: str, limit: int = 50, client: httpx.Client | None = None) -> list[Post]:
    """Return public YouTube videos matching `keyword`. Raises SourceUnavailable."""
    own = client is None
    if own:
        client = httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
    try:
        resp = client.get(SEARCH_URL, params={
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "maxResults": min(limit, 50),
            "order": "date",
            "key": _api_key(),
        })
        if resp.status_code == 403:
            raise SourceUnavailable("YouTube quota exceeded or key invalid (HTTP 403)")
        if resp.status_code != 200:
            raise SourceUnavailable(f"YouTube search failed (HTTP {resp.status_code})")
        return parse(resp.json())
    except httpx.HTTPError as e:
        raise SourceUnavailable(f"YouTube network error: {type(e).__name__}") from e
    finally:
        if own:
            client.close()


def parse(data: dict) -> list[Post]:
    posts: list[Post] = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        text = f"{snippet.get('title', '')} {snippet.get('description', '')}".strip()
        if not text:
            continue
        posts.append(Post(
            source="youtube",
            text=text,
            author_ref=hash_author("youtube", snippet.get("channelId", "") or "unknown"),
            hashtags=extract_hashtags(text),
            created_utc=None,
        ))
    return posts
