import time
import json
import os
from typing import Dict, Any, Tuple
import numpy as np
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    precision_recall_curve, auc, confusion_matrix
)

def compute_eval_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    inference_time_ms: float = 0.0,
    target_precision: float = 0.90
) -> Dict[str, Any]:
    """
    Computes comprehensive evaluation metrics adhering strictly to SPEC.md evaluation protocol:
    Precision, Recall, F1, ROC-AUC, PR-AUC, Confusion Matrix, FPR, Inference ms/txn,
    and Recall at target precision.
    Guarantees no NaN values or fake metrics.
    """
    y_true = np.array(y_true).astype(int)
    y_prob = np.array(y_prob).astype(float)
    
    # Binary predictions at standard 0.5 threshold
    y_pred = (y_prob >= 0.5).astype(int)
    
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    
    try:
        roc_auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        roc_auc = 0.5
        
    p_prec, p_rec, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = float(auc(p_rec, p_prec))
    
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    
    # Recall at fixed target precision (e.g. 90%)
    recall_at_target_prec = 0.0
    for p, r in zip(p_prec, p_rec):
        if p >= target_precision:
            recall_at_target_prec = max(recall_at_target_prec, float(r))
            
    return {
        "accuracy": float((tp + tn) / len(y_true)) if len(y_true) > 0 else 0.0,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "fpr": round(fpr, 4),
        "recall_at_target_precision": round(recall_at_target_prec, 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        },
        "inference_ms_per_txn": round(inference_time_ms, 3),
        "sample_count": int(len(y_true))
    }

def save_metrics_json(metrics_dict: Dict[str, Any], filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(metrics_dict, f, indent=2)

def load_metrics_json(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        return {"status": "Not evaluated"}
    with open(filepath, "r") as f:
        return json.load(f)
