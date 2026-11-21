"""Tests for Stage A step 15 (place intelligence). Offline, using a fake server."""

import httpx
import pytest

from services.place_intel import PlaceNotFound, lookup_place

# Sample Nominatim response for "Loni Kalbhor, Pune".
GEO = [{
    "name": "Loni Kalbhor",
    "lat": "18.4793",
    "lon": "74.0276",
    "type": "village",
    "addresstype": "village",
    "address": {
        "village": "Loni Kalbhor",
        "state_district": "Pune",
        "state": "Maharashtra",
        "country": "India",
    },
}]

WIKI = {
    "type": "standard",
    "title": "Loni Kalbhor",
    "extract": "Loni Kalbhor is a village in the Pune district of Maharashtra, India.",
}


def fake(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_builds_facts_from_sources():
    def handler(request):
        if "nominatim" in request.url.host:
            return httpx.Response(200, json=GEO)
        return httpx.Response(200, json=WIKI)

    facts = lookup_place("Loni Kalbhor, Pune", client=fake(handler))
    assert facts.name == "Loni Kalbhor"
    assert facts.state == "Maharashtra"
    assert facts.district == "Pune"
    assert facts.place_type == "village"
    assert facts.lat == pytest.approx(18.4793)
    assert "village in the Pune district" in facts.summary
    assert facts.sources == ["nominatim", "wikipedia"]


def test_place_not_found_when_geocode_empty():
    def handler(request):
        return httpx.Response(200, json=[])

    with pytest.raises(PlaceNotFound):
        lookup_place("asdkjhaskdjh nowhere", client=fake(handler))


def test_empty_query_rejected():
    with pytest.raises(PlaceNotFound):
        lookup_place("   ", client=fake(lambda r: httpx.Response(200, json=[])))


def test_works_without_wikipedia_article():
    # Geocode succeeds, but Wikipedia has no standard article: still return facts.
    def handler(request):
        if "nominatim" in request.url.host:
            return httpx.Response(200, json=GEO)
        return httpx.Response(404, text="not found")

    facts = lookup_place("Loni Kalbhor", client=fake(handler))
    assert facts.summary is None
    assert facts.sources == ["nominatim"]
    assert facts.state == "Maharashtra"


def test_disambiguation_page_is_ignored():
    def handler(request):
        if "nominatim" in request.url.host:
            return httpx.Response(200, json=GEO)
        return httpx.Response(200, json={"type": "disambiguation", "extract": "could be many things"})

    facts = lookup_place("Loni Kalbhor", client=fake(handler))
    assert facts.summary is None


def test_to_dict_is_json_friendly():
    def handler(request):
        if "nominatim" in request.url.host:
            return httpx.Response(200, json=GEO)
        return httpx.Response(200, json=WIKI)

    d = lookup_place("Loni Kalbhor", client=fake(handler)).to_dict()
    assert d["name"] == "Loni Kalbhor" and isinstance(d["landmarks"], list)
