"""Step 23: generate synthetic, noisy, LABELLED profiles.

Why synthetic: to measure how well the profiling + entity-resolution code works,
we need data where we KNOW the right answer. Doing this on real strangers would
be both impossible to verify and a privacy violation. Here we invent the people,
so the ground truth is ours and nobody real is involved.

The generator injects realistic mess: typos, nicknames, duplicate accounts,
missing fields, and overlapping vocabulary between occupations.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from services.profiling.types import OCCUPATIONS, Profile

# Vocabulary that leans toward each occupation (deliberately overlapping, so the
# task is non-trivial — e.g. both students and teachers say "exam", "class").
VOCAB: dict[str, list[str]] = {
    "student": ["exam", "assignment", "hostel", "fest", "backlog", "semester",
                "internship", "placement", "campus", "notes", "submission", "viva"],
    "teacher": ["lecture", "syllabus", "students", "class", "grading", "attendance",
                "lesson", "school", "homework", "exam", "staffroom", "curriculum"],
    "researcher": ["paper", "dataset", "experiment", "conference", "citation",
                   "hypothesis", "thesis", "lab", "publication", "review", "grant"],
    "industry": ["deadline", "sprint", "client", "deploy", "standup", "release",
                 "manager", "product", "ticket", "meeting", "office", "salary"],
    "other": ["weekend", "movie", "food", "trip", "family", "festival", "cricket",
              "shopping", "traffic", "weather", "music", "recipe"],
}

HASHTAGS: dict[str, list[str]] = {
    "student": ["#studentlife", "#exams", "#collegefest", "#placements"],
    "teacher": ["#teaching", "#edchat", "#classroom", "#teacherlife"],
    "researcher": ["#research", "#phdlife", "#academia", "#openscience"],
    "industry": ["#devlife", "#startup", "#tech", "#remotework"],
    "other": ["#weekendvibes", "#foodie", "#travel", "#cricket"],
}

# Typical active hours (students/industry skew late; teachers earlier).
HOURS: dict[str, tuple[int, int]] = {
    "student": (10, 2), "teacher": (7, 18), "researcher": (9, 23),
    "industry": (9, 22), "other": (8, 23),
}


# How much the occupations bleed into each other. Higher = harder, more realistic.
OWN_VOCAB_PROB = 0.40       # chance a post word comes from the true occupation
CROSS_VOCAB_PROB = 0.30     # chance it comes from a DIFFERENT occupation
TYPO_PROB = 0.12


def _noisy(word: str, rng: random.Random) -> str:
    """Occasionally introduce a typo (swap two letters)."""
    if len(word) > 3 and rng.random() < TYPO_PROB:
        i = rng.randrange(len(word) - 1)
        return word[:i] + word[i + 1] + word[i] + word[i + 2:]
    return word


def _hour(label: str, rng: random.Random) -> int:
    lo, hi = HOURS[label]
    if lo <= hi:
        return rng.randint(lo, hi)
    span = (24 - lo) + hi                      # wraps past midnight
    h = lo + rng.randint(0, span)
    return h % 24


def _pick_pool(label: str, rng: random.Random) -> list[str]:
    """Pick which vocabulary a word is drawn from (with cross-occupation bleed)."""
    r = rng.random()
    if r < OWN_VOCAB_PROB:
        return VOCAB[label]
    if r < OWN_VOCAB_PROB + CROSS_VOCAB_PROB:
        other = rng.choice([o for o in OCCUPATIONS if o != label])
        return VOCAB[other]
    return VOCAB["other"]                       # generic chit-chat


def make_profile(label: str, rng: random.Random, n_posts: int = 12) -> Profile:
    posts, hours, tags = [], [], []
    for _ in range(n_posts):
        words = [_noisy(rng.choice(_pick_pool(label, rng)), rng)
                 for _ in range(rng.randint(4, 9))]
        posts.append(" ".join(words))
        hours.append(_hour(label, rng))
        # Hashtags are noisy too: sometimes the "wrong" occupation's tag.
        if rng.random() < 0.4:
            tag_label = label if rng.random() < 0.7 else rng.choice(OCCUPATIONS)
            tags.append(rng.choice(HASHTAGS[tag_label]))
    # Missing-field mess: sometimes no hashtags.
    if rng.random() < 0.25:
        tags = []
    return Profile(posts=posts, post_hours=hours, hashtags=tags, label=label)


@dataclass
class Dataset:
    profiles: list[Profile]

    @property
    def labels(self) -> list[str]:
        return [p.label for p in self.profiles]


def generate(n: int = 1000, seed: int = 42) -> Dataset:
    """Make `n` labelled profiles, balanced across occupations. Reproducible."""
    rng = random.Random(seed)
    profiles = []
    for i in range(n):
        label = OCCUPATIONS[i % len(OCCUPATIONS)]
        profiles.append(make_profile(label, rng, n_posts=rng.randint(3, 8)))
    rng.shuffle(profiles)
    return Dataset(profiles=profiles)


def make_duplicate(profile: Profile, rng: random.Random) -> Profile:
    """A second 'account' of the same person: same leanings, reworded + noisier.

    Used to test entity resolution (step 19 was for users; here it's for the
    profiling benchmark). Same label, overlapping but not identical content.
    """
    label = profile.label
    dup = make_profile(label, rng, n_posts=max(5, len(profile.posts) - 2))
    # Share a few exact posts so they're linkable but not trivially identical.
    shared = rng.sample(profile.posts, min(2, len(profile.posts)))
    dup.posts[: len(shared)] = shared
    return dup
