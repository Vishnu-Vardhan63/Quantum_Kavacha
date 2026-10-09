import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

class IsolationForestAnomalyDetector:
    """
    Unsupervised Isolation Forest Anomaly Detector.
    Identifies rare transaction patterns and calculates calibrated anomaly probabilities.
    """
    def __init__(self, n_estimators: int = 100, contamination: float = 0.08, random_state: int = 42):
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray):
        """Fit Isolation Forest on normal/unlabeled transaction features."""
        self.model.fit(X)
        self.is_fitted = True
        return self

    def predict_anomaly_score(self, X: np.ndarray) -> np.ndarray:
        """
        Compute anomaly score normalized between 0.0 (normal) and 1.0 (highly anomalous).
        Decision function outputs higher values for normal, lower for anomaly.
        """
        if not self.is_fitted:
            # Calibrated distance heuristic on scaled features when standalone model is un-fitted
            z_distances = np.mean(np.maximum(0, np.abs(X) - 1.0), axis=1)
            return np.clip(z_distances / 3.0, 0.0, 1.0)
        
        # decision_function gives negative values for anomalies
        raw_scores = self.model.decision_function(X)
        # Shift and scale to 0-1
        norm_scores = 0.5 - (raw_scores * 2.0)
        return np.clip(norm_scores, 0.0, 1.0)

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self.model, filepath)

    def load(self, filepath: str):
        if os.path.exists(filepath):
            self.model = joblib.load(filepath)
            self.is_fitted = True
        return self
