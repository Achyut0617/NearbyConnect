"""Shared shape for Stage B platform sources.

Every source returns a list of Post objects. We keep an author_ref ONLY so the
aggregator can count DISTINCT authors for the k-author privacy threshold; it is
hashed and never leaves services/trends.py in any output.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field


class SourceUnavailable(Exception):
    """Raised when a source can't be used (e.g. missing API key, network down)."""


@dataclass
class Post:
    source: str                       # "reddit" | "youtube"
    text: str                         # title + body / description (public content)
    author_ref: str                   # hashed; for distinct-author counting only
    hashtags: list[str] = field(default_factory=list)
    created_utc: float | None = None


def hash_author(source: str, raw_id: str) -> str:
    """One-way hash so we can count distinct authors without keeping identities."""
    return hashlib.sha256(f"{source}:{raw_id}".encode()).hexdigest()[:16]


HASHTAG_RE = re.compile(r"#(\w{2,50})")


def extract_hashtags(text: str) -> list[str]:
    return [f"#{m.lower()}" for m in HASHTAG_RE.findall(text or "")]
