import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app.utils.metrics import compute_eval_metrics, save_metrics_json

class HybridFraudEnsemble:
    """
    Stacking Hybrid Meta-Learner combining:
    1. Classical XGBoost Probability
    2. Deep Learning Autoencoder Anomaly Score
    3. Graph Neural Network (GNN) Probability
    4. Quantum Kernel Anomaly / QSVC Score
    5. Behavioral Anomaly Score (Z-Score)
    
    Includes Platt/Isotonic probability calibration and ablation benchmarking.
    Configurable Risk Thresholds:
      - NORMAL: < 40
      - SUSPICIOUS: 40 - 69
      - HIGH RISK: >= 70
    """
    FEATURE_NAMES = ["xgboost_prob", "autoencoder_anomaly", "gnn_prob", "quantum_anomaly", "behavioral_anomaly"]

    def __init__(self, manual_weights: float = None):
        self.meta_learner = LogisticRegression(class_weight="balanced", random_state=42)
        self.calibrator = IsotonicRegression(out_of_bounds="clip")
        self.weights = {}
        self.manual_weights = manual_weights
        self.is_fitted = False

    def fit(self, meta_X_val: np.ndarray, y_val: np.ndarray) -> "HybridFraudEnsemble":
        """
        Fits meta-learner on out-of-fold validation set to prevent data leakage.
        """
        self.meta_learner.fit(meta_X_val, y_val)
        raw_probs = self.meta_learner.predict_proba(meta_X_val)[:, 1]
        
        # Fit Isotonic Calibrator
        self.calibrator.fit(raw_probs, y_val)
        
        # Extract learned weights
        coefs = self.meta_learner.coef_[0]
        abs_coefs = np.abs(coefs)
        norm_weights = abs_coefs / (np.sum(abs_coefs) + 1e-8)
        
        self.weights = {
            name: round(float(w), 4) for name, w in zip(self.FEATURE_NAMES, norm_weights)
        }
        self.is_fitted = True
        return self

    def predict_risk_score(self, meta_X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Returns (calibrated_probs_0_to_1, risk_scores_0_to_100, risk_levels).
        """
        if not self.is_fitted:
            # Fallback simple weighted average if meta-learner not fitted
            weights = np.array([0.35, 0.20, 0.20, 0.15, 0.10])
            raw_probs = np.dot(meta_X, weights)
            calibrated_probs = raw_probs
        else:
            raw_probs = self.meta_learner.predict_proba(meta_X)[:, 1]
            calibrated_probs = self.calibrator.transform(raw_probs)

        calibrated_probs = np.clip(calibrated_probs, 0.0, 1.0)
        risk_scores = calibrated_probs * 100.0

        risk_levels = []
        for s in risk_scores:
            if s >= 70.0:
                risk_levels.append("HIGH RISK")
            elif s >= 40.0:
                risk_levels.append("SUSPICIOUS")
            else:
                risk_levels.append("NORMAL")

        return calibrated_probs, risk_scores, risk_levels
