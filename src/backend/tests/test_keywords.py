"""Tests for Stage A step 16 (keyword/hashtag extraction)."""

from services.keywords import extract_terms, to_hashtag
from services.place_intel import PlaceFacts


def make_facts(**kw):
    base = dict(
        query="Loni Kalbhor, Pune",
        name="Loni Kalbhor",
        district="Pune",
        state="Maharashtra",
        summary="Loni Kalbhor is known for its engineering colleges and a historic temple.",
        landmarks=["Vishwakarma Institute"],
    )
    base.update(kw)
    return PlaceFacts(**base)


def test_to_hashtag():
    assert to_hashtag("Loni Kalbhor") == "#lonikalbhor"
    assert to_hashtag("Pune!!!") == "#pune"
    assert to_hashtag("   ") == ""


def test_name_ranks_highest():
    terms = extract_terms(make_facts())
    assert terms.keywords[0] == "Loni Kalbhor"       # W_NAME is the biggest weight
    assert "Pune" in terms.keywords


def test_landmark_and_summary_words_included():
    terms = extract_terms(make_facts())
    assert "Vishwakarma Institute" in terms.keywords
    assert any("colleges" in k or "engineering" in k for k in terms.keywords)


def test_categories_boost_terms():
    terms = extract_terms(make_facts(summary=None, landmarks=[]), categories=["education", "culture"])
    assert "education" in terms.keywords and "culture" in terms.keywords


def test_hashtags_start_with_place():
    terms = extract_terms(make_facts())
    assert terms.hashtags[0] == "#lonikalbhor"
    assert "#pune" in terms.hashtags
    assert all(h.startswith("#") for h in terms.hashtags)


def test_stopwords_removed():
    terms = extract_terms(make_facts(summary="It is in the district and known for the the the"))
    assert "the" not in terms.keywords and "and" not in terms.keywords


def test_limit_respected():
    terms = extract_terms(make_facts(), limit=3)
    assert len(terms.keywords) <= 3


def test_handles_minimal_facts():
    terms = extract_terms(PlaceFacts(query="Nowhere", name=None, summary=None))
    assert terms.keywords == [] and terms.place == "Nowhere"
