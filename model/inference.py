"""
model/inference.py — Standalone inference wrapper.

Useful for batch processing or CLI usage outside FastAPI.

Usage:
    python -m model.inference --ndvi-delta -0.25 --ndwi-delta 0.10
"""

import argparse
import os
from typing import Optional

try:
    import joblib
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class ChangeDetectorModel:
    """Thin wrapper around the trained sklearn model."""

    def __init__(self, weights_path: str = "model/weights/change_detector.pkl"):
        self._model = None
        self._path = weights_path
        if SKLEARN_AVAILABLE and os.path.exists(weights_path):
            self._model = joblib.load(weights_path)
            print(f"[Model] Loaded from {weights_path}")
        else:
            print(f"[Model] Weights not found at {weights_path} — run model/train.py first")

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def predict(
        self,
        ndvi_delta: float,
        ndwi_delta: float,
        sensitivity: float = 0.5,
        source_idx: int = 1,
    ) -> Optional[dict]:
        """
        Returns:
            {"change_type": str, "confidence": float} or None if model not loaded
        """
        if not self.loaded:
            return None
        features = np.array([[ndvi_delta, ndwi_delta, sensitivity, source_idx]])
        pred  = self._model.predict(features)[0]
        proba = float(max(self._model.predict_proba(features)[0]))
        return {"change_type": pred, "confidence": round(proba, 3)}

    def predict_batch(self, feature_rows: list) -> list:
        """
        feature_rows: list of [ndvi_delta, ndwi_delta, sensitivity, source_idx]
        Returns list of {"change_type": str, "confidence": float}
        """
        if not self.loaded:
            return []
        import numpy as np
        X = np.array(feature_rows)
        preds  = self._model.predict(X)
        probas = self._model.predict_proba(X).max(axis=1)
        return [
            {"change_type": p, "confidence": round(float(c), 3)}
            for p, c in zip(preds, probas)
        ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run single change-type inference")
    parser.add_argument("--ndvi-delta", type=float, required=True)
    parser.add_argument("--ndwi-delta", type=float, required=True)
    parser.add_argument("--sensitivity", type=float, default=0.5)
    parser.add_argument("--source-idx", type=int, default=1,
                        help="0=Landsat,1=Sentinel2,2=MODIS,3=Sentinel1")
    parser.add_argument("--weights", type=str, default="model/weights/change_detector.pkl")
    args = parser.parse_args()

    model = ChangeDetectorModel(args.weights)
    result = model.predict(args.ndvi_delta, args.ndwi_delta, args.sensitivity, args.source_idx)
    if result:
        print(f"change_type : {result['change_type']}")
        print(f"confidence  : {result['confidence']:.0%}")
    else:
        print("Model not loaded. Run model/train.py first.")
