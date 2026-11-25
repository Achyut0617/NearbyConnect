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


from services.geoapify_client import parse_features  # noqa: E402

SAMPLE = {"features": [
    {"properties": {"name": "Cafe Good Luck", "lat": 18.52, "lon": 73.85,
                    "categories": ["catering", "catering.cafe"],
                    "datasource": {"raw": {"osm_type": "n", "osm_id": 11}}}},
    # coordinates only in geometry ([lon, lat])
    {"properties": {"name": "Shaniwar Wada", "place_id": "abc",
                    "categories": ["tourism.sights.fort"]},
     "geometry": {"type": "Point", "coordinates": [73.855, 18.519]}},
    {"properties": {"categories": ["catering.cafe"], "lat": 1, "lon": 2}},     # no name
    {"properties": {"name": "Car Wash", "categories": ["service.vehicle"],
                    "lat": 1, "lon": 2}},                                        # unmapped
    {"properties": {"name": "Nowhere", "categories": ["catering.cafe"]}},       # no coords
]}


def test_parse_features_matches_osm_shape():
    places = parse_features(SAMPLE)
    assert places == [
        {"osm_id": "n/11", "name": "Cafe Good Luck", "type_key": "amenity",
         "type": "cafe", "lat": 18.52, "lon": 73.85},
        {"osm_id": "geoapify/abc", "name": "Shaniwar Wada", "type_key": "historic",
         "type": "fort", "lat": 18.519, "lon": 73.855},
    ]


def test_parse_empty_response():
    assert parse_features({}) == []
