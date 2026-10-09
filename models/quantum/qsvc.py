import os
import sys
import joblib
import numpy as np
from typing import Dict, Any, Tuple
from sklearn.svm import SVC

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.quantum.quantum_kernel import QuantumKernelEngine

class QSVCWrapper:
    """
    Supervised Quantum Support Vector Classifier (QSVC) using precomputed Quantum Kernel matrix.
    Stores support vectors so predicting a single new transaction requires computing kernel
    only against the support vector subset.
    """
    def __init__(self, kernel_engine: QuantumKernelEngine, C: float = 1.0):
        self.kernel_engine = kernel_engine
        self.C = C
        self.model = SVC(kernel="precomputed", C=self.C, probability=True, random_state=42)
        self.support_vectors_data = None
        self.is_fitted = False

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> "QSVCWrapper":
        self.X_train_raw = X_train
        K_train = self.kernel_engine.evaluate(X_train)
        self.model.fit(K_train, y_train)
        
        # Save raw support vectors data for efficient test inference
        sv_indices = self.model.support_
        self.support_vectors_data = X_train[sv_indices]
        self.is_fitted = True
        return self

    def predict_proba(self, X_test: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("QSVCWrapper must be fitted before predict_proba.")
            
        K_test = self.kernel_engine.evaluate(X_test, self.X_train_raw)
        return self.model.predict_proba(K_test)

    def predict_single(self, x_new: np.ndarray) -> Tuple[float, int]:
        """
        Scores a single new transaction against trained support vectors / training set.
        Returns (fraud_probability, binary_label).
        """
        if x_new.ndim == 1:
            x_new = x_new.reshape(1, -1)
            
        K_single = self.kernel_engine.evaluate(x_new, self.X_train_raw)
        prob = float(self.model.predict_proba(K_single)[0, 1])
        pred = int(prob >= 0.5)
        return prob, pred
