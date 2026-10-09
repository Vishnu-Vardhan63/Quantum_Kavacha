import os
import sys
import numpy as np
from typing import Dict, Any, Tuple
from sklearn.svm import OneClassSVM

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.quantum.quantum_kernel import QuantumKernelEngine

class QuantumAnomalyDetector:
    """
    Unsupervised Quantum Anomaly Detector using OneClassSVM trained on legitimate-only data.
    Computes quantum_anomaly_score in [0, 1] based on quantum feature space decision distance.
    Also returns kernel similarity to k nearest legitimate neighbors for risk factor explanations.
    """
    def __init__(self, kernel_engine: QuantumKernelEngine, nu: float = 0.05):
        self.kernel_engine = kernel_engine
        self.nu = nu
        self.model = OneClassSVM(kernel="precomputed", nu=self.nu)
        self.X_legit_train = None
        self.is_fitted = False

    def fit(self, X_legit: np.ndarray) -> "QuantumAnomalyDetector":
        self.X_legit_train = X_legit
        K_legit = self.kernel_engine.evaluate(X_legit)
        self.model.fit(K_legit)
        self.is_fitted = True
        return self

    def score_samples(self, X_test: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("QuantumAnomalyDetector must be fitted before scoring samples.")
            
        K_test = self.kernel_engine.evaluate(X_test, self.X_legit_train)
        dec_func = self.model.decision_function(K_test)
        
        # Convert decision function to anomaly score normalized in [0, 1]
        # Lower decision function = more anomalous
        anomaly_score = 1.0 / (1.0 + np.exp(dec_func))
        return anomaly_score

    def explain_sample(self, x_new: np.ndarray, k: int = 5) -> Dict[str, Any]:
        """
        Computes quantum kernel similarity to k nearest legitimate training samples.
        Provides transparent quantum-similarity-based risk explanation without hardcoding.
        """
        if x_new.ndim == 1:
            x_new = x_new.reshape(1, -1)
            
        K_sim = self.kernel_engine.evaluate(x_new, self.X_legit_train)[0]
        top_k_indices = np.argsort(K_sim)[-k:][::-1]
        top_k_similarities = K_sim[top_k_indices].tolist()
        
        avg_legit_similarity = float(np.mean(top_k_similarities))
        anomaly_score = float(1.0 / (1.0 + np.exp(self.model.decision_function(K_sim.reshape(1, -1))[0])))
        
        return {
            "quantum_anomaly_score": round(anomaly_score, 4),
            "avg_legit_quantum_similarity": round(avg_legit_similarity, 4),
            "top_k_similarities": [round(s, 4) for s in top_k_similarities],
            "quantum_explanation_text": (
                f"Quantum feature map fidelity to nearest legitimate clusters is {avg_legit_similarity*100:.1f}%. "
                f"Anomaly score: {anomaly_score:.3f}."
            )
        }
