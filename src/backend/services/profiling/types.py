"""Shared types for the author-profiling model (Stage C).

A Profile is the ONLY input the model sees. It is built either from a licensed
public benchmark row, or from a NearbyConnect user's OWN account with consent.
It intentionally carries NO name, location, or contact — only public post text,
the hours posts were made, and hashtags.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# The occupation classes we predict. "other" catches everyone else.
OCCUPATIONS = ("student", "teacher", "researcher", "industry", "other")


@dataclass
class Profile:
    posts: list[str] = field(default_factory=list)      # public post text
    post_hours: list[int] = field(default_factory=list)  # 0-23, local hour of each post
    hashtags: list[str] = field(default_factory=list)    # e.g. ["#exam", "#research"]
    label: str | None = None                             # true occupation (training/eval only)

    @property
    def text(self) -> str:
        return " ".join(self.posts)
