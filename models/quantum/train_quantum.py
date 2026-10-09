import os
import sys

# Ensure project root in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any

from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split

import xgboost as xgb

from backend.app.utils.preprocessing import DatasetAdapter
from backend.app.utils.metrics import compute_eval_metrics, save_metrics_json
from models.quantum.quantum_kernel import QuantumKernelEngine
from models.quantum.qsvc import QSVCWrapper
from models.quantum.quantum_anomaly import QuantumAnomalyDetector

def train_and_eval_quantum_pipeline(
    data_path: str = None,
    num_qubits: int = 4,
    sample_budget: int = 600
) -> Dict[str, Any]:
    """
    Executes complete Milestone 3 Quantum Kernel Pipeline:
    Preprocess -> Feature selection -> PCA to 4 qubits -> MinMaxScaler to [0, 2pi]
    -> zz_feature_map -> FidelityStatevectorKernel -> QSVC + Quantum OneClassSVM.
    Also computes fair benchmarks against classical RBF-SVM and XGBoost on identical PCA features.
    """
    if data_path is None:
        data_path = os.path.join(project_root, "data", "sample", "demo_transactions.csv")
        
    df = pd.read_csv(data_path)
    adapter = DatasetAdapter(df)
    X, y = adapter.prepare_features()
    
    # Stratified subsample to respect compute budget
    if len(X) > sample_budget:
        X_sub, _, y_sub, _ = train_test_split(
            X, y, train_size=sample_budget, stratify=y, random_state=42
        )
    else:
        X_sub, y_sub = X.copy(), y.copy()
        
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_sub, y_sub, test_size=0.3, stratify=y_sub, random_state=42
    )

    # PCA reduction to 4 qubits
    pca = PCA(n_components=num_qubits, random_state=42)
    X_train_pca = pca.fit_transform(X_train_raw)
    X_test_pca = pca.transform(X_test_raw)
    
    # Scale into rotation range [0, 2*pi]
    scaler = MinMaxScaler(feature_range=(0, 2 * np.pi))
    X_train_q = scaler.fit_transform(X_train_pca)
    X_test_q = scaler.transform(X_test_pca)

    # Create Quantum Kernel Engine with Qiskit 2.x API zz_feature_map
    kernel_engine = QuantumKernelEngine(
        num_qubits=num_qubits,
        map_type="zz",
        reps=2,
        entanglement="linear"
    )
    
    artifacts_dir = os.path.join(project_root, "model_artifacts", "quantum")
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # Evaluate training & test kernel matrices
    t0 = time.time()
    K_train = kernel_engine.evaluate(X_train_q)
    kernel_calc_time = time.time() - t0
    
    # Verify mathematical properties of kernel matrix (Symmetric, PSD, Diagonal=1)
    kernel_verification = kernel_engine.verify_kernel_matrix(K_train)
    print(f"Quantum Kernel Verification: {kernel_verification}")
    
    # Save a sample 30x30 kernel matrix for Quantum Lab Heatmap display
    sample_k = K_train[:min(30, len(K_train)), :min(30, len(K_train))]
    np.save(os.path.join(artifacts_dir, "kernel_matrix_sample.npy"), sample_k)

    # 1. Supervised QSVC Head
    qsvc = QSVCWrapper(kernel_engine=kernel_engine, C=1.0)
    qsvc.fit(X_train_q, y_train.values)
    
    t0 = time.time()
    qsvc_probs = qsvc.predict_proba(X_test_q)[:, 1]
    qsvc_infer_time = (time.time() - t0) / len(X_test_q) * 1000.0
    qsvc_metrics = compute_eval_metrics(y_test, qsvc_probs, qsvc_infer_time)
    
    # 2. Unsupervised Quantum OneClassSVM Head (trained on legit-only)
    X_legit_train = X_train_q[y_train == 0]
    quantum_ad = QuantumAnomalyDetector(kernel_engine=kernel_engine, nu=0.05)
    quantum_ad.fit(X_legit_train)
    
    t0 = time.time()
    q_anomaly_scores = quantum_ad.score_samples(X_test_q)
    q_ad_infer_time = (time.time() - t0) / len(X_test_q) * 1000.0
    quantum_ad_metrics = compute_eval_metrics(y_test, q_anomaly_scores, q_ad_infer_time)

    # 3. FAIR BENCHMARK: Classical RBF-SVM on SAME subsample and SAME 4-qubit PCA features
    rbf_svm = SVC(kernel="rbf", probability=True, random_state=42)
    rbf_svm.fit(X_train_q, y_train)
    t0 = time.time()
    rbf_probs = rbf_svm.predict_proba(X_test_q)[:, 1]
    rbf_infer_time = (time.time() - t0) / len(X_test_q) * 1000.0
    rbf_metrics = compute_eval_metrics(y_test, rbf_probs, rbf_infer_time)

    # 4. FAIR BENCHMARK: XGBoost on SAME subsample and SAME 4-qubit PCA features
    xgb_benchmark = xgb.XGBClassifier(n_estimators=50, random_state=42, eval_metric="logloss")
    xgb_benchmark.fit(X_train_q, y_train)
    t0 = time.time()
    xgb_probs = xgb_benchmark.predict_proba(X_test_q)[:, 1]
    xgb_infer_time = (time.time() - t0) / len(X_test_q) * 1000.0
    xgb_metrics = compute_eval_metrics(y_test, xgb_probs, xgb_infer_time)

    # Compile quantum benchmark metrics dictionary
    quantum_metrics_results = {
        "QSVC (Quantum Kernel)": {**qsvc_metrics, "execution_mode": "SIMULATION", "qubits": num_qubits},
        "Quantum OneClassSVM (Anomaly)": {**quantum_ad_metrics, "execution_mode": "SIMULATION", "qubits": num_qubits},
        "Classical RBF-SVM (Same PCA Subsample)": {**rbf_metrics, "execution_mode": "CLASSICAL_BASELINE"},
        "XGBoost (Same PCA Subsample)": {**xgb_metrics, "execution_mode": "CLASSICAL_BASELINE"}
    }
    
    save_metrics_json(quantum_metrics_results, os.path.join(artifacts_dir, "metrics.json"))

    # Save real circuit telemetry
    circuit_telemetry = kernel_engine.get_circuit_telemetry()
    circuit_telemetry["verification"] = kernel_verification
    circuit_telemetry["sample_budget"] = len(X_sub)
    circuit_telemetry["pca_components"] = num_qubits
    
    with open(os.path.join(artifacts_dir, "circuit_info.json"), "w") as f:
        json.dump(circuit_telemetry, f, indent=2)

    # Save fitted models and transformers
    joblib.dump(pca, os.path.join(artifacts_dir, "pca_transformer.joblib"))
    joblib.dump(scaler, os.path.join(artifacts_dir, "minmax_scaler.joblib"))
    joblib.dump(qsvc, os.path.join(artifacts_dir, "qsvc_model.joblib"))
    joblib.dump(quantum_ad, os.path.join(artifacts_dir, "quantum_anomaly_model.joblib"))
    
    print(f"Quantum Kernel Pipeline successfully trained and evaluated.")
    print(f"Metrics saved to {os.path.join(artifacts_dir, 'metrics.json')}")
    return quantum_metrics_results

if __name__ == "__main__":
    train_and_eval_quantum_pipeline()
