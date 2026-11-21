"""Stage A+B endpoint (Step 19): place facts + aggregate area trends.

GET /area-intel?place=Loni Kalbhor, Pune
  -> trusted facts about the place (Wikipedia/Wikidata/OSM) + derived keywords

GET /area-trends?place=Loni Kalbhor, Pune
  -> the above PLUS aggregate-only social trends (Reddit/YouTube), with the
     k-author privacy threshold. Sources with no API key are skipped, not errors.

No per-person data is ever returned. Requires login (keeps the scraper gated).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from auth import get_current_user
from models.user import User
from services.keywords import extract_terms
from services.place_intel import PlaceNotFound, lookup_place
from services.sources import reddit, youtube
from services.sources.base import SourceUnavailable
from services.trends import aggregate

router = APIRouter()

# How many top keywords to actually search on each platform.
SEARCH_TERMS = 3
PER_TERM_LIMIT = 50


@router.get("/area-intel")
def area_intel(place: str = Query(..., min_length=2, max_length=120),
               _: User = Depends(get_current_user)):
    try:
        facts = lookup_place(place)
    except PlaceNotFound:
        raise HTTPException(404, f"Couldn't find trusted info for {place!r}.")
    terms = extract_terms(facts)
    return {"facts": facts.to_dict(), "terms": terms.to_dict()}


@router.get("/area-trends")
def area_trends(place: str = Query(..., min_length=2, max_length=120),
                _: User = Depends(get_current_user)):
    try:
        facts = lookup_place(place)
    except PlaceNotFound:
        raise HTTPException(404, f"Couldn't find trusted info for {place!r}.")

    terms = extract_terms(facts)
    search_terms = terms.keywords[:SEARCH_TERMS] or [facts.name or place]

    posts = []
    sources_used: list[str] = []
    skipped: dict[str, str] = {}
    for name, module in (("reddit", reddit), ("youtube", youtube)):
        got_any = False
        for term in search_terms:
            try:
                posts.extend(module.search(term, limit=PER_TERM_LIMIT))
                got_any = True
            except SourceUnavailable as e:
                skipped[name] = str(e)
                break  # same key problem will repeat; don't retry other terms
        if got_any:
            sources_used.append(name)

    trends = aggregate(facts.name or place, posts, sources_used)
    result = {"facts": facts.to_dict(), "terms": terms.to_dict(), "trends": trends.to_dict()}
    if skipped:
        result["sources_skipped"] = skipped  # e.g. {"youtube": "API key not set"}
    return result
