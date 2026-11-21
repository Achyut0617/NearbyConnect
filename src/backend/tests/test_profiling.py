"""Tests for Stage C profiling: synthetic data, features, v1 formula, v2 model."""

import random

import pytest

from services.profiling.estimate import estimate
from services.profiling.features import FEATURE_NAMES, extract_features, feature_vector
from services.profiling.model import OccupationModel
from services.profiling.synthetic import generate, make_duplicate, make_profile
from services.profiling.types import OCCUPATIONS, Profile


# ---------- synthetic data ----------

def test_generate_is_reproducible():
    a = generate(n=50, seed=1).labels
    b = generate(n=50, seed=1).labels
    assert a == b                      # same seed -> same data


def test_generate_balanced_and_labelled():
    data = generate(n=100, seed=3)
    assert len(data.profiles) == 100
    assert set(data.labels) == set(OCCUPATIONS)
    assert all(p.label in OCCUPATIONS for p in data.profiles)


def test_duplicate_shares_some_posts():
    rng = random.Random(0)
    original = make_profile("student", rng, n_posts=8)
    dup = make_duplicate(original, rng)
    assert dup.label == "student"
    assert set(original.posts) & set(dup.posts)        # linkable


# ---------- features ----------

def test_feature_vector_length_and_order():
    p = make_profile("researcher", random.Random(5))
    feats = extract_features(p)
    assert set(feats) == set(FEATURE_NAMES)
    assert feature_vector(p) == [feats[n] for n in FEATURE_NAMES]


def test_features_handle_empty_profile():
    feats = extract_features(Profile())
    assert all(isinstance(v, float) for v in feats.values())   # no divide-by-zero


# ---------- v1 explainable estimator ----------

def test_estimate_probabilities_sum_to_one():
    e = estimate(make_profile("industry", random.Random(7)))
    assert abs(sum(e.probabilities.values()) - 1.0) < 1e-6
    assert e.label in OCCUPATIONS
    assert 0 <= e.confidence <= 1


def test_estimate_gives_reasons():
    e = estimate(make_profile("student", random.Random(8)))
    assert len(e.reasons) >= 1
    assert e.to_dict()["basis"] == "estimated"


def test_estimate_beats_random_on_a_batch():
    data = generate(n=300, seed=11)
    correct = sum(1 for p in data.profiles if estimate(p).label == p.label)
    assert correct / len(data.profiles) > 0.5          # well above 1/5 random


def test_clear_student_profile_predicts_student():
    p = Profile(posts=["exam assignment hostel backlog semester viva"] * 6,
                post_hours=[1, 2, 0, 23, 1, 2], hashtags=["#studentlife", "#exams"])
    assert estimate(p).label == "student"


# ---------- v2 trained model ----------

def test_trained_model_predicts_and_persists(tmp_path):
    data = generate(n=600, seed=2)
    model = OccupationModel.train(data.profiles, seed=0)
    e = model.predict(data.profiles[0])
    assert e.label in OCCUPATIONS
    assert abs(sum(e.probabilities.values()) - 1.0) < 1e-6

    path = tmp_path / "m.joblib"
    model.save(path)
    assert OccupationModel.exists(path)
    reloaded = OccupationModel.load(path)
    assert reloaded.predict(data.profiles[0]).label == e.label   # same after reload


@pytest.mark.slow
def test_trained_model_accuracy_on_holdout():
    from sklearn.model_selection import train_test_split
    data = generate(n=2000, seed=9)
    train, test = train_test_split(data.profiles, test_size=0.25, random_state=9,
                                   stratify=data.labels)
    model = OccupationModel.train(train, seed=9)
    acc = sum(1 for p in test if model.predict(p).label == p.label) / len(test)
    assert acc > 0.8                                   # trained model should be strong
