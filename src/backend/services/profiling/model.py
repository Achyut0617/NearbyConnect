"""Step 22: occupation estimator v2 — a trained scikit-learn model.

A logistic-regression classifier over the same features as v1. It LEARNS the
weights from labelled data instead of us hand-setting them, then we compare the
two approaches on a held-out test set (see scripts/train_profiling.py).

The trained model is saved to a .joblib file so the API can load it at startup.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from services.profiling.estimate import Estimate
from services.profiling.features import FEATURE_NAMES, feature_vector
from services.profiling.types import Profile

# Default location for the saved model (kept out of git; built by the script).
MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "occupation_model.joblib"


class OccupationModel:
    def __init__(self, clf: LogisticRegression, scaler: StandardScaler, classes: list[str]):
        self.clf = clf
        self.scaler = scaler
        self.classes = classes

    # ---- training ----
    @classmethod
    def train(cls, profiles: list[Profile], c: float = 1.0, seed: int = 0) -> "OccupationModel":
        X = np.array([feature_vector(p) for p in profiles], dtype=float)
        y = np.array([p.label for p in profiles])
        scaler = StandardScaler().fit(X)
        clf = LogisticRegression(max_iter=1000, C=c, random_state=seed)
        clf.fit(scaler.transform(X), y)
        return cls(clf, scaler, list(clf.classes_))

    # ---- prediction ----
    def predict(self, profile: Profile) -> Estimate:
        x = self.scaler.transform([feature_vector(profile)])
        probs = self.clf.predict_proba(x)[0]
        prob_map = {cls_: float(p) for cls_, p in zip(self.clf.classes_, probs)}
        top = max(prob_map, key=prob_map.get)
        reasons = self._reasons(profile, top)
        return Estimate(probabilities=prob_map, label=top,
                        confidence=prob_map[top], reasons=reasons)

    def _reasons(self, profile: Profile, label: str) -> list[str]:
        """Explain by which features pushed hardest toward the predicted class."""
        idx = list(self.clf.classes_).index(label)
        coefs = self.clf.coef_[idx]
        x = self.scaler.transform([feature_vector(profile)])[0]
        contrib = sorted(
            ((coefs[i] * x[i], FEATURE_NAMES[i]) for i in range(len(FEATURE_NAMES))),
            reverse=True,
        )
        out = [name.replace("_", " ") for amt, name in contrib[:3] if amt > 0]
        return out or ["low-confidence prediction"]

    # ---- persistence ----
    def save(self, path: Path = MODEL_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"clf": self.clf, "scaler": self.scaler, "classes": self.classes}, path)
        return path

    @classmethod
    def load(cls, path: Path = MODEL_PATH) -> "OccupationModel":
        data = joblib.load(path)
        return cls(data["clf"], data["scaler"], data["classes"])

    @staticmethod
    def exists(path: Path = MODEL_PATH) -> bool:
        return Path(path).is_file()
