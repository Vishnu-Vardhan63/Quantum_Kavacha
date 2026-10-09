import os
import pandas as pd
from typing import List, Dict, Any
from fastapi import APIRouter
from backend.app.services.simulation_service import simulation_service
from backend.app.services.fraud_engine import fraud_engine
from backend.app.schemas.transaction import TransactionPayload
from backend.app.core.config import settings

router = APIRouter(prefix="/api", tags=["Fraud Alerts"])

@router.get("/fraud-alerts", summary="Get Live Severity-Sorted Fraud Alerts")
async def get_fraud_alerts():
    alerts = []
    
    # Check simulation memory buffer
    for item in simulation_service.buffer:
        pred = item["prediction"]
        if pred["risk_level"] in ["HIGH RISK", "SUSPICIOUS"]:
            alerts.append({
                "txn_id": pred["txn_id"],
                "risk_score": pred["risk_score"],
                "risk_level": pred["risk_level"],
                "decision": pred["decision"],
                "amount": item["transaction"]["amount"],
                "timestamp": item["timestamp"],
                "risk_factors": pred["risk_factors"],
                "confirmation": "CONFIRMED" if pred["risk_score"] > 80 else "UNCONFIRMED — AI ONLY"
            })
            
    if not alerts:
        # Fallback to demo transactions
        sample_path = os.path.join(settings.DATA_DIR, "sample", "demo_transactions.csv")
        if os.path.exists(sample_path):
            df = pd.read_csv(sample_path)
            fraud_df = df[df["label"] == 1].head(15)
            for idx, row in fraud_df.iterrows():
                payload = TransactionPayload(
                    txn_id=str(row["txn_id"]),
                    user_id=str(row["user_id"]),
                    account_id=str(row.get("account_id", f"ACC-{idx}")),
                    device_id=str(row.get("device_id", f"DEV-{idx}")),
                    ip=str(row.get("ip", "192.168.1.1")),
                    merchant_id=str(row.get("merchant_id", "MERCH-1")),
                    lat=float(row.get("lat", 19.076)),
                    lon=float(row.get("lon", 72.877)),
                    amount=float(row["amount"]),
                    hour=int(row["hour"]),
                    velocity_1h=int(row.get("velocity_1h", 12)),
                    account_age_days=int(row.get("account_age_days", 40)),
                    device_score=float(row.get("device_score", 0.78)),
                    location_score=float(row.get("location_score", 0.82)),
                    merchant_risk=float(row.get("merchant_risk", 0.76))
                )
                pred = fraud_engine.predict(payload)
                alerts.append({
                    "txn_id": pred.txn_id,
                    "risk_score": pred.risk_score,
                    "risk_level": pred.risk_level,
                    "decision": pred.decision,
                    "amount": payload.amount,
                    "timestamp": 1700000000.0,
                    "risk_factors": pred.risk_factors,
                    "confirmation": "CONFIRMED" if pred.risk_score > 80 else "UNCONFIRMED — AI ONLY"
                })

    # Sort severity desc
    alerts.sort(key=lambda x: x["risk_score"], reverse=True)
    return alerts
