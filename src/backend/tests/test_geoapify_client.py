"""Tests for services/geoapify_client.py (backup places provider, step 26)."""

from services.geoapify_client import CATEGORY_MAP, REQUEST_CATEGORIES, osm_type_for


def test_most_specific_category_wins():
    assert osm_type_for(["catering", "catering.cafe"]) == ("amenity", "cafe")
    assert osm_type_for(["tourism", "tourism.sights", "tourism.sights.fort"]) == (
        "historic", "fort")


def test_unknown_categories_are_skipped():
    assert osm_type_for(["building", "service.vehicle"]) is None
    assert osm_type_for([]) is None


def test_every_mapping_uses_a_key_the_app_knows():
    from services.osm_client import PLACE_KEYS
    assert {key for key, _ in CATEGORY_MAP.values()} <= set(PLACE_KEYS)


def test_request_covers_every_mapped_top_category():
    assert {c.split(".")[0] for c in CATEGORY_MAP} <= set(REQUEST_CATEGORIES)
