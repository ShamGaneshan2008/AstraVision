"""
model/train.py — Train a RandomForest change-type classifier.

This is a bootstrapped training script using synthetic features.
In production, replace the synthetic data with real extracted features
from labeled Sentinel-2 / Landsat time-series pairs.

Features: [ndvi_delta, ndwi_delta, sensitivity, source_idx]
Labels:   change_type string  (e.g. "deforestation")

Usage:
    python -m model.train
    python -m model.train --samples 5000 --out model/weights/change_detector.pkl
"""

import argparse
import os
import random
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


CHANGE_TYPES = [
    "deforestation",
    "urban_expansion",
    "flood",
    "wildfire",
    "glacial_retreat",
    "agricultural",
    "unknown",
]


def generate_synthetic_samples(n: int = 2000) -> tuple:
    """
    Generate plausible feature–label pairs based on spectral heuristics.
    Replace with real labeled data for production.
    """
    X, y = [], []
    rng = random.Random(42)

    rules = {
        "deforestation":   lambda: (rng.uniform(-0.35, -0.08), rng.uniform(-0.05, 0.04)),
        "wildfire":        lambda: (rng.uniform(-0.55, -0.25), rng.uniform(-0.06, 0.03)),
        "flood":           lambda: (rng.uniform(-0.20, 0.05),  rng.uniform( 0.05, 0.30)),
        "urban_expansion": lambda: (rng.uniform(-0.18, -0.04), rng.uniform(-0.12, -0.02)),
        "glacial_retreat": lambda: (rng.uniform( 0.04, 0.15),  rng.uniform( 0.06, 0.20)),
        "agricultural":    lambda: (rng.uniform(-0.07, 0.07),  rng.uniform(-0.04, 0.04)),
        "unknown":         lambda: (rng.uniform(-0.04, 0.04),  rng.uniform(-0.03, 0.03)),
    }

    per_class = n // len(CHANGE_TYPES)
    for label, fn in rules.items():
        for _ in range(per_class):
            ndvi_d, ndwi_d = fn()
            sens = rng.uniform(0.1, 1.0)
            src  = rng.randint(0, 3)
            # add small gaussian noise
            ndvi_d += rng.gauss(0, 0.015)
            ndwi_d += rng.gauss(0, 0.010)
            X.append([ndvi_d, ndwi_d, sens, src])
            y.append(label)

    return np.array(X), np.array(y)


def train(n_samples: int = 2000, out_path: str = "model/weights/change_detector.pkl"):
    if not SKLEARN_AVAILABLE:
        print("scikit-learn not installed. Run: pip install scikit-learn joblib")
        return

    print(f"Generating {n_samples} synthetic training samples…")
    X, y = generate_synthetic_samples(n_samples)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Training RandomForestClassifier…")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    print("\nClassification report (test set):")
    print(classification_report(y_test, clf.predict(X_test)))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    joblib.dump(clf, out_path)
    print(f"\nModel saved → {out_path}")
    print("Set USE_ML_MODEL=True in .env to enable it.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train change-detection classifier")
    parser.add_argument("--samples", type=int, default=2000, help="Training sample count")
    parser.add_argument("--out", type=str, default="model/weights/change_detector.pkl")
    args = parser.parse_args()
    train(args.samples, args.out)
