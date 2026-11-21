"""Stage B (Step 18): aggregate posts into AREA trends. NO per-person data out.

The privacy rule lives here: a topic or hashtag is reported ONLY if at least
MIN_DISTINCT_AUTHORS different accounts used it. The output contains counts and
topics only — never author references, handles, or post text tied to a person.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from services.keywords import STOPWORDS
from services.sources.base import Post

# A topic/hashtag must come from at least this many DISTINCT authors to appear.
MIN_DISTINCT_AUTHORS = 20

# Tiny, explainable sentiment lexicon (good enough for an area mood gauge).
POSITIVE = {"good", "great", "love", "best", "amazing", "beautiful", "happy",
            "awesome", "nice", "fun", "proud", "win", "celebrate", "favourite"}
NEGATIVE = {"bad", "worst", "hate", "problem", "issue", "dirty", "unsafe",
            "traffic", "pollution", "angry", "sad", "crime", "delay", "broken"}


@dataclass
class Trend:
    term: str
    distinct_authors: int
    mentions: int


@dataclass
class AreaTrends:
    place: str
    sources_used: list[str]
    total_posts: int
    topics: list[Trend] = field(default_factory=list)
    hashtags: list[Trend] = field(default_factory=list)
    sentiment: dict = field(default_factory=dict)
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "place": self.place,
            "sources_used": self.sources_used,
            "total_posts": self.total_posts,
            "topics": [t.__dict__ for t in self.topics],
            "hashtags": [t.__dict__ for t in self.hashtags],
            "sentiment": self.sentiment,
            "note": self.note,
        }


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zA-Z][a-zA-Z]{2,}", text.lower()) if w not in STOPWORDS}


def _sentiment_of(text: str) -> int:
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    return len(words & POSITIVE) - len(words & NEGATIVE)


def _threshold_counts(
    author_sets: dict[str, set[str]], mentions: dict[str, int], min_authors: int, limit: int
) -> list[Trend]:
    """Keep only terms used by >= min_authors DISTINCT authors; rank by that."""
    kept = [
        Trend(term=term, distinct_authors=len(authors), mentions=mentions[term])
        for term, authors in author_sets.items()
        if len(authors) >= min_authors
    ]
    kept.sort(key=lambda t: (-t.distinct_authors, -t.mentions, t.term))
    return kept[:limit]


def aggregate(
    place: str,
    posts: list[Post],
    sources_used: list[str],
    min_authors: int = MIN_DISTINCT_AUTHORS,
    limit: int = 15,
) -> AreaTrends:
    """Build AreaTrends. Enforces the k-author threshold; strips all identities."""
    topic_authors: dict[str, set[str]] = defaultdict(set)
    topic_mentions: dict[str, int] = defaultdict(int)
    tag_authors: dict[str, set[str]] = defaultdict(set)
    tag_mentions: dict[str, int] = defaultdict(int)
    sent_pos = sent_neg = 0

    for p in posts:
        for word in _words(p.text):
            topic_authors[word].add(p.author_ref)
            topic_mentions[word] += 1
        for tag in set(p.hashtags):
            tag_authors[tag].add(p.author_ref)
            tag_mentions[tag] += 1
        s = _sentiment_of(p.text)
        if s > 0:
            sent_pos += 1
        elif s < 0:
            sent_neg += 1

    topics = _threshold_counts(topic_authors, topic_mentions, min_authors, limit)
    hashtags = _threshold_counts(tag_authors, tag_mentions, min_authors, limit)

    rated = sent_pos + sent_neg
    sentiment = {
        "positive": sent_pos,
        "negative": sent_neg,
        "mood": "mixed" if rated == 0 else (
            "mostly positive" if sent_pos > sent_neg * 1.2 else
            "mostly negative" if sent_neg > sent_pos * 1.2 else "mixed"
        ),
    }

    note = ""
    if not topics and not hashtags:
        note = (
            f"Not enough distinct accounts to report anything (need >= {min_authors} "
            "per topic). This protects individuals' privacy."
        )

    return AreaTrends(
        place=place,
        sources_used=sources_used,
        total_posts=len(posts),
        topics=topics,
        hashtags=hashtags,
        sentiment=sentiment,
        note=note,
    )


def contains_identity(trends_dict: dict, author_refs: set[str]) -> bool:
    """Safety check used in tests: no author ref should appear anywhere in output."""
    blob = str(trends_dict)
    return any(ref in blob for ref in author_refs)
