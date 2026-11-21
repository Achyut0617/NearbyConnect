"""Tests for services/scoring.py (Step 6)."""

from services.scoring import categories_for, rank_places, score_place


def place(name, category, type_="x", lat=18.52, lon=73.85):
    return {"name": name, "category": category, "type": type_, "lat": lat, "lon": lon}


COWORK = place("91springboard", "coworking", "coworking")
RESTAURANT = place("Vaishali", "food", "restaurant")


def test_coworking_beats_restaurant_for_startups():
    # The Step 6 "Check" from PLAN.md.
    s_cowork, _ = score_place(COWORK, ["startups"])
    s_food, _ = score_place(RESTAURANT, ["startups"])
    assert s_cowork > s_food


def test_no_interests_means_zero():
    assert score_place(COWORK, []) == (0, [])


def test_unknown_interest_scores_zero_without_name_match():
    assert score_place(COWORK, ["underwater basket weaving"])[0] == 0


def test_name_match_bonus():
    cafe = place("Third Wave Coffee", "cafe", "cafe")
    score, reasons = score_place(cafe, ["coffee"])
    assert score == 3 + 2  # category points + name bonus
    assert "name mentions 'coffee'" in reasons


def test_name_match_needs_whole_word():
    # "ai" must not match inside "Sai".
    temple = place("Sai Baba Mandir", "other", "place_of_worship")
    assert score_place(temple, ["ai"])[0] == 0
    lab = place("Pune AI Lab", "office", "company")
    assert score_place(lab, ["ai"])[0] >= 2


def test_osm_type_counts_as_text():
    bookshop = place("Crossword", "shopping", "books")
    assert score_place(bookshop, ["books"])[0] == 2  # via type "books"


def test_more_matching_interests_score_higher():
    one, _ = score_place(COWORK, ["startups"])
    two, _ = score_place(COWORK, ["startups", "ai"])
    assert two > one


def test_reasons_explain_score():
    _, reasons = score_place(COWORK, ["startups"])
    assert reasons == ["coworking matches 'startups'"]


def test_plural_and_case_lookup():
    assert categories_for("Startup") == categories_for("startups")
    assert categories_for("MUSEUM") == categories_for("museums")
    assert categories_for("nothing-like-this") == {}


def test_rank_sorts_by_score_then_distance():
    near_food = place("Near Food", "food", lat=18.5201)
    far_cowork = place("Far Cowork", "coworking", lat=18.5300)
    near_cowork = place("Near Cowork", "coworking", lat=18.5205)
    ranked = rank_places([near_food, far_cowork, near_cowork], ["startups"],
                         user_lat=18.52, user_lon=73.85)
    assert [p["name"] for p in ranked] == ["Near Cowork", "Far Cowork", "Near Food"]
    assert ranked[0]["distance_m"] < ranked[1]["distance_m"]
    assert "score" in ranked[0] and "reasons" in ranked[0]


def test_rank_without_location_still_works():
    ranked = rank_places([RESTAURANT, COWORK], ["startups"])
    assert ranked[0]["name"] == "91springboard"
    assert ranked[0]["distance_m"] is None
