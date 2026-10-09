import os
import pytest
import numpy as np
import json
from models.quantum.feature_map import create_pluggable_feature_map
from models.quantum.quantum_kernel import QuantumKernelEngine
from models.quantum.qsvc import QSVCWrapper
from models.quantum.quantum_anomaly import QuantumAnomalyDetector
from backend.app.utils.metrics import load_metrics_json

def test_feature_map_creation():
    fm_zz = create_pluggable_feature_map(num_qubits=4, map_type="zz", reps=2, entanglement="linear")
    assert fm_zz.num_qubits == 4
    assert len(fm_zz.parameters) == 4

    fm_pauli = create_pluggable_feature_map(num_qubits=6, map_type="pauli", reps=1, entanglement="linear")
    assert fm_pauli.num_qubits == 6

def test_kernel_matrix_properties():
    kernel_engine = QuantumKernelEngine(num_qubits=4, map_type="zz", reps=2)
    X_sample = np.random.uniform(0, 2*np.pi, size=(10, 4))
    
    K = kernel_engine.evaluate(X_sample)
    assert K.shape == (10, 10)
    
    verification = kernel_engine.verify_kernel_matrix(K)
    assert verification["is_symmetric"] is True
    assert verification["diagonal_ones"] is True
    assert verification["is_psd"] is True
    assert verification["valid"] is True

def test_quantum_heads_4_and_6_qubits():
    for num_qubits in [4, 6]:
        engine = QuantumKernelEngine(num_qubits=num_qubits, map_type="zz", reps=1)
        X_tr = np.random.uniform(0, 2*np.pi, size=(20, num_qubits))
        y_tr = np.array([0]*16 + [1]*4)
        X_te = np.random.uniform(0, 2*np.pi, size=(5, num_qubits))

        # QSVC head
        qsvc = QSVCWrapper(kernel_engine=engine)
        qsvc.fit(X_tr, y_tr)
        probs = qsvc.predict_proba(X_te)[:, 1]
        assert len(probs) == 5
        assert np.all((probs >= 0.0) & (probs <= 1.0))

        # OneClassSVM Anomaly head
        q_ad = QuantumAnomalyDetector(kernel_engine=engine)
        q_ad.fit(X_tr[y_tr == 0])
        scores = q_ad.score_samples(X_te)
        assert len(scores) == 5
        assert np.all((scores >= 0.0) & (scores <= 1.0))

def test_kernel_caching():
    engine = QuantumKernelEngine(num_qubits=4, map_type="zz", reps=1)
    X = np.random.uniform(0, 2*np.pi, size=(8, 4))
    
    # First computation (writes cache)
    K1 = engine.evaluate(X)
    # Second computation (loads from cache)
    K2 = engine.evaluate(X)
    
    assert np.allclose(K1, K2)

def test_quantum_artifacts_and_benchmark():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    artifacts_dir = os.path.join(project_root, "model_artifacts", "quantum")
    
    metrics_path = os.path.join(artifacts_dir, "metrics.json")
    circuit_info_path = os.path.join(artifacts_dir, "circuit_info.json")
    
    assert os.path.exists(metrics_path)
    assert os.path.exists(circuit_info_path)
    
    metrics = load_metrics_json(metrics_path)
    assert "QSVC (Quantum Kernel)" in metrics
    assert "Classical RBF-SVM (Same PCA Subsample)" in metrics
    
    with open(circuit_info_path, "r") as f:
        c_info = json.load(f)
    assert c_info["num_qubits"] == 4
    assert c_info["verification"]["valid"] is True
