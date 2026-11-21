"""Stage A (Step 16): turn place facts into ranked search terms + hashtags.

Input: a PlaceFacts (from place_intel) and optionally nearby place categories
(from the existing osm_client/clean pipeline).
Output: ranked keywords and hashtags to drive Stage B's AGGREGATE area search.

No people here. These are area terms like #punefoodie, "Loni Kalbhor",
college names, "heritage". Simple frequency/importance scoring first.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

# Very common English words to ignore when mining the summary text.
STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "at", "is", "are", "was", "were", "and",
    "or", "to", "for", "with", "by", "from", "as", "it", "its", "this", "that",
    "near", "which", "also", "has", "have", "had", "been", "be", "city", "town",
    "village", "district", "state", "india", "located", "situated", "known",
}

# Weights: where a term came from decides how important it is.
W_NAME = 5.0
W_DISTRICT = 3.0
W_LANDMARK = 3.0
W_CATEGORY = 2.0
W_SUMMARY = 1.0


@dataclass
class AreaTerms:
    place: str
    keywords: list[str]        # ranked, human-readable search terms
    hashtags: list[str]        # ranked #hashtags

    def to_dict(self) -> dict:
        return {"place": self.place, "keywords": self.keywords, "hashtags": self.hashtags}


def to_hashtag(text: str) -> str:
    """'Loni Kalbhor' -> '#lonikalbhor'. Keeps only letters and digits."""
    cleaned = re.sub(r"[^a-z0-9]", "", text.lower())
    return f"#{cleaned}" if cleaned else ""


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-zA-Z][a-zA-Z0-9]+", text.lower()) if w not in STOPWORDS]


def extract_terms(facts, categories: list[str] | None = None, limit: int = 15) -> AreaTerms:
    """Build ranked keywords + hashtags from place facts and nearby categories.

    `facts` is a PlaceFacts (or anything with the same attributes).
    `categories` is an optional list like ["cafe", "education", "culture"].
    """
    scores: Counter[str] = Counter()

    name = getattr(facts, "name", None)
    if name:
        scores[name] += W_NAME
    district = getattr(facts, "district", None)
    if district:
        scores[district] += W_DISTRICT
    for lm in getattr(facts, "landmarks", []) or []:
        scores[lm] += W_LANDMARK
    for cat in categories or []:
        scores[cat.replace("_", " ")] += W_CATEGORY

    summary = getattr(facts, "summary", None)
    if summary:
        for word, count in Counter(_words(summary)).items():
            if len(word) > 2:
                scores[word] += W_SUMMARY * count

    ranked = [term for term, _ in scores.most_common(limit)]

    # Hashtags: from the best single-token terms + a couple of fixed area tags.
    hashtags: list[str] = []
    seen: set[str] = set()
    for term in ([name, district] if name else []) + ranked:
        if not term:
            continue
        tag = to_hashtag(term)
        if tag and tag not in seen:
            seen.add(tag)
            hashtags.append(tag)

    return AreaTerms(place=name or facts.query, keywords=ranked, hashtags=hashtags[:limit])
