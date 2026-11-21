"""Tests for services/clean.py, using deliberately messy input."""

from services.clean import CATEGORIES, categorize, clean_places, distance_m


def place(osm_id, name, type_key="amenity", type_="cafe", lat=18.5200, lon=73.8500):
    """Helper to build a place dict shaped like osm_client's output."""
    return {"osm_id": osm_id, "name": name, "type_key": type_key,
            "type": type_, "lat": lat, "lon": lon}


# ---------- dropping bad entries ----------

def test_drops_missing_blank_and_non_text_names():
    raw = [
        place("node/1", None),
        place("node/2", ""),
        place("node/3", "    "),
        place("node/4", 12345),
        place("node/5", "Real Cafe"),
    ]
    assert [p["name"] for p in clean_places(raw)] == ["Real Cafe"]


def test_drops_bad_coordinates():
    raw = [
        place("node/1", "No Lat", lat=None),
        place("node/2", "Impossible Lat", lat=200),
        place("node/3", "Text Lon", lon="73.85"),
        place("node/4", "Good One"),
    ]
    assert [p["name"] for p in clean_places(raw)] == ["Good One"]


# ---------- tidying ----------

def test_trims_and_collapses_spaces_in_names():
    out = clean_places([place("node/1", "  Cafe    Mocha \n")])
    assert out[0]["name"] == "Cafe Mocha"


def test_does_not_change_the_input_list():
    raw = [place("node/1", "  Spaced  ")]
    clean_places(raw)
    assert raw[0]["name"] == "  Spaced  "
    assert "category" not in raw[0]


# ---------- de-duplication ----------

def test_removes_same_osm_id():
    raw = [place("node/1", "Cafe A"), place("node/1", "Cafe A")]
    assert len(clean_places(raw)) == 1


def test_removes_same_name_very_close_even_with_different_id_and_case():
    # Same cafe mapped as a point AND as a building, about 20 m apart.
    raw = [
        place("node/1", "Blue Tokai", lat=18.52000, lon=73.85000),
        place("way/9", "BLUE  tokai", lat=18.52018, lon=73.85000),
    ]
    out = clean_places(raw)
    assert len(out) == 1
    assert out[0]["osm_id"] == "node/1"  # first one is kept


def test_keeps_same_name_far_apart():
    # Two branches of a chain, about 1 km apart: both are real places.
    raw = [
        place("node/1", "Starbucks", lat=18.5200, lon=73.8500),
        place("node/2", "Starbucks", lat=18.5290, lon=73.8500),
    ]
    assert len(clean_places(raw)) == 2


def test_keeps_different_names_at_same_spot():
    # A mall with several shops at one point.
    raw = [place("node/1", "Book Shop"), place("node/2", "Shoe Shop")]
    assert len(clean_places(raw)) == 2


# ---------- categories ----------

def test_categorize_known_tags():
    assert categorize("amenity", "restaurant") == "food"
    assert categorize("amenity", "cafe") == "cafe"
    assert categorize("office", "coworking") == "coworking"
    assert categorize("amenity", "coworking_space") == "coworking"
    assert categorize("amenity", "library") == "education"
    assert categorize("amenity", "community_centre") == "event_space"
    assert categorize("tourism", "museum") == "culture"
    assert categorize("leisure", "park") == "outdoors"
    assert categorize("leisure", "fitness_centre") == "fitness"


def test_categorize_falls_back_on_key():
    assert categorize("shop", "books") == "shopping"
    assert categorize("office", "it") == "office"
    assert categorize("shop", "coffee") == "cafe"  # exact match wins over fallback


def test_categorize_unknown_and_messy():
    assert categorize("amenity", "bench") == "other"
    assert categorize(None, None) == "other"
    assert categorize(" Amenity ", "CAFE ") == "cafe"


def test_every_category_used_is_in_the_fixed_set():
    raw = [place(f"n/{i}", f"P{i}", k, v, lat=18.5 + i * 0.01) for i, (k, v) in enumerate([
        ("amenity", "cafe"), ("shop", "books"), ("office", "it"),
        ("leisure", "park"), ("amenity", "bench"), ("tourism", "museum"),
    ])]
    for p in clean_places(raw):
        assert p["category"] in CATEGORIES


# ---------- full messy example ----------

def test_full_messy_list():
    raw = [
        place("node/1", "  Third Wave Coffee ", "amenity", "cafe"),
        place("way/1", "third wave coffee", "amenity", "cafe", lat=18.52010),  # dup ~11 m
        place("node/2", None, "amenity", "restaurant"),                         # no name
        place("node/3", "91springboard", "office", "coworking", lat=18.53),
        place("node/3", "91springboard", "office", "coworking", lat=18.53),     # same id
        place("node/4", "Pune Central Library", "amenity", "library", lat=18.54),
        place("node/5", "Bad Spot", lat=999),                                   # bad coords
    ]
    out = clean_places(raw)
    assert [(p["name"], p["category"]) for p in out] == [
        ("Third Wave Coffee", "cafe"),
        ("91springboard", "coworking"),
        ("Pune Central Library", "education"),
    ]


# ---------- distance helper ----------

def test_distance_zero_and_known_value():
    assert distance_m(18.52, 73.85, 18.52, 73.85) == 0
    # 0.001 degrees of latitude is about 111 m anywhere on Earth.
    assert 110 < distance_m(18.520, 73.85, 18.521, 73.85) < 112
