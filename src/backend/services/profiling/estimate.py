"""Step 21: occupation estimator v1 — an explainable Bayes-style formula.

Idea (naive Bayes in log space):
  score(occ) = log(prior) + sum over evidence of log-likelihood-ratio
Each piece of evidence (vocab share, hashtags, posting time) nudges the odds
toward or away from each occupation. We convert scores to probabilities with
softmax, and keep the TOP reasons so every answer can explain itself.

No training needed: the weights are hand-set and inspectable. This is the
"invent your own mathematical factors" piece, kept fully transparent.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from services.profiling.features import extract_features
from services.profiling.types import OCCUPATIONS, Profile

# Equal prior: we assume nothing about occupation before seeing posts.
PRIOR = {occ: 1.0 / len(OCCUPATIONS) for occ in OCCUPATIONS}

# How strongly each feature pushes toward its occupation.
VOCAB_WEIGHT = 6.0
TAG_WEIGHT = 4.0
TIME_WEIGHT = 1.5


@dataclass
class Estimate:
    probabilities: dict[str, float]     # occupation -> probability (sums to 1)
    label: str                          # the top occupation
    confidence: float                   # probability of the top one
    reasons: list[str]                  # human-readable "because ..." lines
    basis: str = "estimated"            # "estimated" (inferred) vs "confirmed"

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "basis": self.basis,
            "probabilities": {k: round(v, 3) for k, v in self.probabilities.items()},
            "reasons": self.reasons,
        }


def _softmax(scores: dict[str, float]) -> dict[str, float]:
    top = max(scores.values())
    exp = {k: math.exp(v - top) for k, v in scores.items()}
    total = sum(exp.values())
    return {k: v / total for k, v in exp.items()}


def estimate(profile: Profile) -> Estimate:
    """Predict occupation probabilities with explanations."""
    feats = extract_features(profile)
    scores = {occ: math.log(PRIOR[occ]) for occ in OCCUPATIONS}
    contributions: dict[str, list[tuple[float, str]]] = {occ: [] for occ in OCCUPATIONS}

    for occ in OCCUPATIONS:
        v = feats[f"vocab_{occ}"]
        if v > 0:
            amt = VOCAB_WEIGHT * v
            scores[occ] += amt
            contributions[occ].append((amt, f"uses {occ}-related words ({v:.0%} of posts)"))
        t = feats[f"tag_{occ}"]
        if t > 0:
            amt = TAG_WEIGHT * t
            scores[occ] += amt
            contributions[occ].append((amt, f"uses {occ} hashtags"))

    # Posting-time nudges (soft, since they overlap a lot).
    if feats["frac_latenight"] > 0.3:
        scores["student"] += TIME_WEIGHT * feats["frac_latenight"]
        contributions["student"].append(
            (TIME_WEIGHT * feats["frac_latenight"], "often posts late at night"))
    if feats["frac_workhours"] > 0.5:
        for occ in ("industry", "teacher"):
            scores[occ] += TIME_WEIGHT * feats["frac_workhours"] * 0.5
        contributions["industry"].append(
            (TIME_WEIGHT * feats["frac_workhours"] * 0.5, "posts mostly during work hours"))

    probs = _softmax(scores)
    top = max(probs, key=probs.get)
    reasons = [text for _, text in sorted(contributions[top], reverse=True)[:3]]
    if not reasons:
        reasons = ["not enough signal; this is a low-confidence guess"]

    return Estimate(probabilities=probs, label=top, confidence=probs[top], reasons=reasons)
