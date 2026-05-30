from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd


class MLScoringAgent:
    """
    ML Scoring Agent

    Purpose:
    - Loads tabular_model.joblib
    - Handles the artifact format saved by ml/train_all.py
    - Produces ml_score for the LangGraph workflow
    """

    def __init__(self, artifact_path: str = "artifacts/tabular_model.joblib"):
        self.artifact_path = Path(artifact_path)
        self.model = None
        self.encoder = None
        self.num_cols = []
        self.cat_cols = []
        self.version = "random_forest_v1"

        if not self.artifact_path.exists():
            print(f"MLScoringAgent warning: missing {self.artifact_path}")
            return

        payload = joblib.load(self.artifact_path)

        # train_all.py saves:
        # {"model": model, "encoder": encoder, "num_cols": num_cols, "cat_cols": cat_cols}
        if isinstance(payload, dict):
            self.model = payload.get("model")
            self.encoder = payload.get("encoder")
            self.num_cols = payload.get("num_cols", [])
            self.cat_cols = payload.get("cat_cols", [])
        else:
            # fallback if artifact is directly a sklearn model
            self.model = payload

    def predict(self, features: Dict[str, Any]) -> float:
        """
        Predict fraud probability from features.
        """

        if self.model is None:
            return 0.0

        try:
            row = pd.DataFrame([features])

            # If artifact has training-time preprocessing
            if self.encoder is not None and self.num_cols and self.cat_cols:
                for col in self.num_cols:
                    if col not in row.columns:
                        row[col] = 0.0

                for col in self.cat_cols:
                    if col not in row.columns:
                        row[col] = "unknown"

                X_num = row[self.num_cols].to_numpy(dtype=np.float32)
                X_cat = self.encoder.transform(row[self.cat_cols])
                X = np.hstack([X_num, X_cat])

                score = self.model.predict_proba(X)[0][1]
                return round(float(score), 4)

            # Fallback for direct sklearn model
            if hasattr(self.model, "predict_proba"):
                score = self.model.predict_proba(row)[0][1]
                return round(float(score), 4)

            if hasattr(self.model, "predict"):
                score = self.model.predict(row)[0]
                return round(float(score), 4)

            return 0.0

        except Exception as exc:
            print(f"MLScoringAgent prediction failed: {exc}")
            return 0.0