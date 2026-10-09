import os
import pytest
import joblib
from backend.app.utils.metrics import load_metrics_json

def test_classical_model_artifacts_exist():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    artifacts_dir = os.path.join(project_root, "model_artifacts", "classical")
    
    assert os.path.exists(os.path.join(artifacts_dir, "scaler.joblib"))
    assert os.path.exists(os.path.join(artifacts_dir, "logistic_regression.joblib"))
    assert os.path.exists(os.path.join(artifacts_dir, "random_forest.joblib"))
    assert os.path.exists(os.path.join(artifacts_dir, "metrics.json"))

def test_metrics_json_integrity():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    metrics_path = os.path.join(project_root, "model_artifacts", "classical", "metrics.json")
    metrics = load_metrics_json(metrics_path)
    
    assert "Logistic Regression" in metrics
    assert "Random Forest" in metrics
    for model_name, m in metrics.items():
        assert "pr_auc" in m
        assert "roc_auc" in m
        assert "inference_ms_per_txn" in m
        assert "confusion_matrix" in m
