"""Step 20: turn a Profile into numeric features.

Features are deliberately simple and explainable (good for the v1 formula and
as input to the v2 model):
- share of posts in each occupation's signal vocabulary
- hashtag category counts
- posting-time profile (share of posts late at night, morning, work hours)
- basic volume/vocabulary-richness signals
"""

from __future__ import annotations

import re

from services.profiling.synthetic import HASHTAGS, VOCAB
from services.profiling.types import OCCUPATIONS, Profile

FEATURE_NAMES = (
    [f"vocab_{occ}" for occ in OCCUPATIONS]
    + [f"tag_{occ}" for occ in OCCUPATIONS]
    + ["frac_latenight", "frac_morning", "frac_workhours", "post_count", "vocab_richness"]
)

_WORD = re.compile(r"[a-zA-Z]+")
# Flatten each occupation's vocab into a set for fast lookup.
_VOCAB_SETS = {occ: set(words) for occ, words in VOCAB.items()}
_TAG_SETS = {occ: set(tags) for occ, tags in HASHTAGS.items()}


def _tokens(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text)]


def extract_features(profile: Profile) -> dict[str, float]:
    """Return a {feature_name: value} dict for one profile."""
    tokens = _tokens(profile.text)
    n_tokens = len(tokens) or 1
    feats: dict[str, float] = {}

    # Share of words that belong to each occupation's signal vocabulary.
    for occ in OCCUPATIONS:
        hits = sum(1 for t in tokens if t in _VOCAB_SETS[occ])
        feats[f"vocab_{occ}"] = hits / n_tokens

    # Hashtag category counts (normalised by number of hashtags).
    tags = [t.lower() for t in profile.hashtags]
    n_tags = len(tags) or 1
    for occ in OCCUPATIONS:
        feats[f"tag_{occ}"] = sum(1 for t in tags if t in _TAG_SETS[occ]) / n_tags

    # Posting-time profile.
    hours = profile.post_hours or []
    n_hours = len(hours) or 1
    feats["frac_latenight"] = sum(1 for h in hours if h >= 23 or h <= 3) / n_hours
    feats["frac_morning"] = sum(1 for h in hours if 6 <= h <= 10) / n_hours
    feats["frac_workhours"] = sum(1 for h in hours if 10 <= h <= 18) / n_hours

    # Volume + vocabulary richness.
    feats["post_count"] = float(len(profile.posts))
    feats["vocab_richness"] = len(set(tokens)) / n_tokens

    return feats


def feature_vector(profile: Profile) -> list[float]:
    """Features as an ordered list (same order as FEATURE_NAMES)."""
    feats = extract_features(profile)
    return [feats[name] for name in FEATURE_NAMES]
