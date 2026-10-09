import os
import pandas as pd
from typing import Dict, Any
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.services.simulation_service import simulation_service
from backend.app.utils.metrics import load_metrics_json

router = APIRouter(prefix="/api", tags=["Analytics"])

@router.get("/analytics", summary="Get High-Level System Fraud Analytics")
async def get_analytics():
    sample_path = os.path.join(settings.DATA_DIR, "sample", "demo_transactions.csv")
    total_txns = 1200
    fraud_count = 95
    
    if os.path.exists(sample_path):
        df = pd.read_csv(sample_path)
        total_txns = len(df)
        fraud_count = int(df["label"].sum())

    suspicious_count = int(total_txns * 0.08)
    avg_risk_score = 14.2
    fraud_rate_pct = round((fraud_count / max(1, total_txns)) * 100.0, 2)

    # Quantum vs Classical summary
    q_metrics = load_metrics_json(os.path.join(settings.ARTIFACTS_DIR, "quantum", "metrics.json"))
    qsvc_m = q_metrics.get("QSVC (Quantum Kernel)", {})
    rbf_m = q_metrics.get("Classical RBF-SVM (Same PCA Subsample)", {})

    return {
        "total_transactions": total_txns + len(simulation_service.buffer),
        "fraud_detected": fraud_count,
        "suspicious_flagged": suspicious_count,
        "fraud_rate_percent": fraud_rate_pct,
        "average_risk_score": avg_risk_score,
        "quantum_analyzed_count": total_txns,
        "quantum_vs_classical": {
            "quantum_pr_auc": qsvc_m.get("pr_auc", "Not evaluated"),
            "quantum_roc_auc": qsvc_m.get("roc_auc", "Not evaluated"),
            "classical_pr_auc": rbf_m.get("pr_auc", "Not evaluated"),
            "classical_roc_auc": rbf_m.get("roc_auc", "Not evaluated")
        },
        "risk_distribution": {
            "NORMAL": total_txns - fraud_count - suspicious_count,
            "SUSPICIOUS": suspicious_count,
            "HIGH_RISK": fraud_count
        },
        "volume_trend": [
            {"hour": "00:00", "count": 45, "fraud": 8},
            {"hour": "04:00", "count": 12, "fraud": 2},
            {"hour": "08:00", "count": 120, "fraud": 4},
            {"hour": "12:00", "count": 310, "fraud": 12},
            {"hour": "16:00", "count": 420, "fraud": 15},
            {"hour": "20:00", "count": 280, "fraud": 24},
            {"hour": "23:00", "count": 95, "fraud": 30}
        ]
    }
