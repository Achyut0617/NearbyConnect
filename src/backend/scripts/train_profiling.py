"""Train + evaluate the occupation profiling models (Steps 21-22).

Run from src/backend:
    python -m scripts.train_profiling --n 4000

What it does:
1. Generates N labelled synthetic profiles (reproducible).
2. Splits into train/test.
3. Evaluates v1 (explainable Bayes formula, no training) on the test set.
4. Trains v2 (logistic regression) on the train set, evaluates on the test set.
5. Prints an accuracy + calibration comparison, and saves v2 to a .joblib file.

Everything here uses SYNTHETIC data with known labels — no real people.
"""

from __future__ import annotations

import argparse

from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from services.profiling.estimate import estimate
from services.profiling.model import OccupationModel
from services.profiling.synthetic import generate


def calibration_error(pairs: list[tuple[float, bool]], bins: int = 10) -> float:
    """Expected Calibration Error: are the confidences honest?

    pairs = [(confidence, was_correct), ...]. Lower is better.
    """
    buckets: list[list[tuple[float, bool]]] = [[] for _ in range(bins)]
    for conf, correct in pairs:
        buckets[min(bins - 1, int(conf * bins))].append((conf, correct))
    total = len(pairs) or 1
    ece = 0.0
    for b in buckets:
        if not b:
            continue
        avg_conf = sum(c for c, _ in b) / len(b)
        acc = sum(1 for _, ok in b if ok) / len(b)
        ece += (len(b) / total) * abs(avg_conf - acc)
    return ece


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4000, help="number of synthetic profiles")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    data = generate(n=args.n, seed=args.seed)
    train, test = train_test_split(
        data.profiles, test_size=0.25, random_state=args.seed,
        stratify=[p.label for p in data.profiles],
    )
    y_true = [p.label for p in test]
    print(f"Generated {args.n} synthetic profiles -> {len(train)} train / {len(test)} test\n")

    # --- v1: explainable Bayes formula (no training) ---
    v1 = [estimate(p) for p in test]
    v1_pred = [e.label for e in v1]
    v1_acc = accuracy_score(y_true, v1_pred)
    v1_ece = calibration_error([(e.confidence, e.label == t) for e, t in zip(v1, y_true)])

    # --- v2: trained logistic regression ---
    model = OccupationModel.train(train, seed=args.seed)
    v2 = [model.predict(p) for p in test]
    v2_pred = [e.label for e in v2]
    v2_acc = accuracy_score(y_true, v2_pred)
    v2_ece = calibration_error([(e.confidence, e.label == t) for e, t in zip(v2, y_true)])

    print("=== Model comparison (held-out synthetic test set) ===")
    print(f"{'model':<28}{'accuracy':>10}{'calib. err (ECE)':>20}")
    print(f"{'v1 explainable formula':<28}{v1_acc:>10.3f}{v1_ece:>20.3f}")
    print(f"{'v2 logistic regression':<28}{v2_acc:>10.3f}{v2_ece:>20.3f}")
    print("\n(lower ECE = more honest confidence)\n")

    print("=== v2 per-class report ===")
    print(classification_report(y_true, v2_pred, zero_division=0))

    path = model.save()
    print(f"Saved trained model -> {path}")


if __name__ == "__main__":
    main()
