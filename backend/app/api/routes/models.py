import os
import json
from typing import Dict, Any, List
from fastapi import APIRouter, BackgroundTasks, HTTPException
from backend.app.core.config import settings
from backend.app.utils.metrics import load_metrics_json
from scripts.train_all import main as retrain_all_task

router = APIRouter(prefix="/api", tags=["Models & Training"])

training_state = {"status": "idle", "last_run": None, "message": "All models ready."}

def run_retrain_bg():
    global training_state
    training_state["status"] = "running"
    try:
        retrain_all_task()
        training_state["status"] = "completed"
        training_state["message"] = "Retraining completed successfully."
    except Exception as e:
        training_state["status"] = "failed"
        training_state["message"] = str(e)

@router.post("/train", summary="Trigger Background Model Retraining")
async def trigger_training(background_tasks: BackgroundTasks):
    global training_state
    if training_state["status"] == "running":
        return {"status": "already_running", "message": "Model training is currently in progress."}
    
    background_tasks.add_task(run_retrain_bg)
    training_state["status"] = "running"
    training_state["message"] = "Retraining process started in background."
    return training_state

@router.get("/metrics", summary="Get Aggregated System Metrics")
async def get_all_metrics():
    artifacts_dir = settings.ARTIFACTS_DIR
    
    classical = load_metrics_json(os.path.join(artifacts_dir, "classical", "metrics.json"))
    deep = load_metrics_json(os.path.join(artifacts_dir, "deep_learning", "metrics.json"))
    graph = load_metrics_json(os.path.join(artifacts_dir, "graph", "metrics.json"))
    quantum = load_metrics_json(os.path.join(artifacts_dir, "quantum", "metrics.json"))
    ensemble = load_metrics_json(os.path.join(artifacts_dir, "ensemble", "metrics.json"))

    return {
        "classical": classical,
        "deep_learning": deep,
        "graph": graph,
        "quantum": quantum,
        "ensemble": ensemble
    }

@router.get("/models/comparison", summary="Get Model Comparison Table Data")
async def get_model_comparison():
    all_metrics = await get_all_metrics()
    comparison_table = []

    categories = [
        ("classical", all_metrics.get("classical", {})),
        ("deep_learning", all_metrics.get("deep_learning", {})),
        ("graph", all_metrics.get("graph", {})),
        ("quantum", all_metrics.get("quantum", {})),
        ("ensemble", all_metrics.get("ensemble", {}))
    ]

    for cat_name, models_dict in categories:
        if isinstance(models_dict, dict):
            for model_name, m in models_dict.items():
                if model_name == "learned_weights":
                    continue
                if isinstance(m, dict) and "accuracy" in m:
                    comparison_table.append({
                        "model_name": model_name,
                        "category": cat_name,
                        "accuracy": m.get("accuracy", 0.0),
                        "precision": m.get("precision", 0.0),
                        "recall": m.get("recall", 0.0),
                        "f1": m.get("f1", 0.0),
                        "roc_auc": m.get("roc_auc", 0.0),
                        "pr_auc": m.get("pr_auc", 0.0),
                        "inference_ms": m.get("inference_ms_per_txn", 0.0),
                        "execution_mode": m.get("execution_mode", "CLASSICAL")
                    })

    return comparison_table

@router.get("/models", summary="List Available Models")
async def list_models():
    artifacts_dir = settings.ARTIFACTS_DIR
    models_status = []
    
    check_list = [
        ("Logistic Regression", "classical", "logistic_regression.joblib"),
        ("Random Forest", "classical", "random_forest.joblib"),
        ("XGBoost", "classical", "xgboost.joblib"),
        ("Autoencoder", "deep_learning", "autoencoder.pt"),
        ("Dense NN", "deep_learning", "dense_nn.pt"),
        ("GraphSAGE (GNN)", "graph", "graphsage.pt"),
        ("QSVC (Quantum Kernel)", "quantum", "qsvc_model.joblib"),
        ("Quantum OneClassSVM", "quantum", "quantum_anomaly_model.joblib"),
        ("Hybrid Stacking Ensemble", "ensemble", "hybrid_ensemble.joblib")
    ]

    for name, cat, filename in check_list:
        path = os.path.join(artifacts_dir, cat, filename)
        is_ready = os.path.exists(path)
        models_status.append({
            "name": name,
            "category": cat,
            "status": "READY" if is_ready else "NOT_TRAINED",
            "artifact_path": path
        })

    return models_status
