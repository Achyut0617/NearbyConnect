"""Step 24: opt-in self-analysis. A user analyses THEIR OWN account, with consent.

POST /me/analyze   {consent: true, posts: [...], post_hours: [...], hashtags: [...]}
  -> estimated occupation + probabilities + "because ..." reasons, and suggested
     interest tags derived from their own posts.

Hard rules:
- consent MUST be true, or we refuse (422). This is the whole point.
- The input is the user's OWN posts. We never fetch anyone else's.
- Nothing is stored: the posts and the result are used for this response only.
Uses the trained model if one is present, else the explainable v1 formula.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from models.user import User
from services.profiling.estimate import estimate as estimate_v1
from services.profiling.features import extract_features
from services.profiling.model import OccupationModel
from services.profiling.synthetic import VOCAB
from services.profiling.types import OCCUPATIONS, Profile

router = APIRouter()

MAX_POSTS = 500

# Load the trained model once at import, if it was built. Else None -> v1 formula.
_MODEL: OccupationModel | None = OccupationModel.load() if OccupationModel.exists() else None


class AnalyzeBody(BaseModel):
    consent: bool
    posts: list[str] = Field(default_factory=list, max_length=MAX_POSTS)
    post_hours: list[int] = Field(default_factory=list, max_length=MAX_POSTS)
    hashtags: list[str] = Field(default_factory=list, max_length=MAX_POSTS)


def suggest_interests(profile: Profile, top: int = 5) -> list[str]:
    """Pull interest-like words from the user's own posts (their signal vocab)."""
    feats = extract_features(profile)
    tokens = profile.text.lower().split()
    hits = [w for occ in OCCUPATIONS for w in VOCAB[occ] if w in tokens]
    # Keep order of first appearance, de-duped.
    seen, out = set(), []
    for w in hits:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out[:top]


@router.post("/me/analyze")
def analyze_self(body: AnalyzeBody, _: User = Depends(get_current_user)):
    if not body.consent:
        raise HTTPException(422, "Analysis needs your explicit consent (consent=true).")
    if not body.posts:
        raise HTTPException(422, "Send at least one of your own posts to analyse.")

    profile = Profile(posts=body.posts,
                      post_hours=[h for h in body.post_hours if 0 <= h <= 23],
                      hashtags=body.hashtags)

    est = _MODEL.predict(profile) if _MODEL else estimate_v1(profile)
    return {
        "model": "trained-v2" if _MODEL else "formula-v1",
        "occupation": est.to_dict(),
        "suggested_interests": suggest_interests(profile),
        "note": "Estimated from the posts you provided. Nothing was stored.",
    }
