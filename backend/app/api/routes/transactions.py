import os
import pandas as pd
from typing import List, Dict, Any, Optional
import json
import time
from backend.app.db.database import get_db_connection
from fastapi import APIRouter, HTTPException, Query, Path
from backend.app.schemas.transaction import TransactionPayload, PredictionResponse
from backend.app.services.fraud_engine import fraud_engine
from backend.app.services.simulation_service import simulation_service
from backend.app.core.config import settings

router = APIRouter(prefix="/api", tags=["Transactions"])

@router.post("/predict", response_model=PredictionResponse, summary="Score Single Transaction")
async def predict_transaction(payload: TransactionPayload):
    try:
        pred = fraud_engine.predict(payload)
        from backend.app.db.database import MongoPersistence
        MongoPersistence.save_transaction(
            txn_id=pred.txn_id,
            user_id=payload.user_id,
            amount=payload.amount,
            merchant_id=payload.merchant_id,
            device_id=payload.device_id,
            ip=payload.ip,
            timestamp=time.time(),
            risk_score=pred.risk_score,
            decision=pred.decision,
            risk_level=pred.risk_level,
            pred_json=pred.model_dump_json()
        )
        try:
            from backend.app.services.investigation_service import investigation_service
            investigation_service.register_case_from_prediction(pred, payload)
        except Exception:
            pass
        return pred
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions", summary="List Scored Transactions")
async def get_transactions(limit: int = Query(default=50, ge=1, le=500)):
    # Fetch from DB first
    results = []
    with get_db_connection() as conn:
        rows = conn.execute("SELECT prediction_data FROM transactions ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        for row in rows:
            results.append(json.loads(row["prediction_data"]))

    # Combine simulation memory buffer with sample file if needed
    if len(results) < limit:
        sim_results = [item["prediction"] for item in simulation_service.buffer[:limit - len(results)]]
        results.extend(sim_results)

    if len(results) < limit:
        sample_path = os.path.join(settings.DATA_DIR, "sample", "demo_transactions.csv")
        if os.path.exists(sample_path):
            df = pd.read_csv(sample_path)
            for idx, row in df.head(limit - len(results)).iterrows():
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
                    velocity_1h=int(row.get("velocity_1h", 1)),
                    account_age_days=int(row.get("account_age_days", 100)),
                    device_score=float(row.get("device_score", 0.1)),
                    location_score=float(row.get("location_score", 0.1)),
                    merchant_risk=float(row.get("merchant_risk", 0.1))
                )
                pred = fraud_engine.predict(payload)
                results.append(pred.model_dump())

    return results

@router.get("/investigation/{transaction_id}", summary="SOC Transaction Investigation")
async def get_transaction_investigation(transaction_id: str = Path(...)):
    # Search memory buffer first
    for item in simulation_service.buffer:
        if item["prediction"]["txn_id"] == transaction_id:
            return {
                "transaction": item["transaction"],
                "prediction": item["prediction"],
                "graph_connections": {
                    "shared_device_users": ["USR-1022", "USR-4011"],
                    "merchant_reputation": "Medium Risk",
                    "ip_cluster_size": 4
                },
                "shap_factors": [
                    {"feature": "amount", "impact": 0.42, "description": "Amount significantly exceeds historical mean"},
                    {"feature": "velocity_1h", "impact": 0.28, "description": "High transaction velocity burst"},
                    {"feature": "location_score", "impact": 0.18, "description": "Unusual geographic distance shift"}
                ]
            }

    # Search demo dataset
    sample_path = os.path.join(settings.DATA_DIR, "sample", "demo_transactions.csv")
    if os.path.exists(sample_path):
        df = pd.read_csv(sample_path)
        match = df[df["txn_id"] == transaction_id]
        if len(match) > 0:
            row = match.iloc[0]
            payload = TransactionPayload(
                txn_id=str(row["txn_id"]),
                user_id=str(row["user_id"]),
                account_id=str(row.get("account_id", "ACC-9901")),
                device_id=str(row.get("device_id", "DEV-9901")),
                ip=str(row.get("ip", "192.168.1.105")),
                merchant_id=str(row.get("merchant_id", "MERCH-8802")),
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
            return {
                "transaction": payload.model_dump(),
                "prediction": pred.model_dump(),
                "graph_connections": {
                    "shared_device_users": ["USR-9901", "USR-9902"],
                    "merchant_reputation": "High Risk Merchant",
                    "ip_cluster_size": 12
                },
                "shap_factors": [
                    {"feature": "amount", "impact": 0.45, "description": "INR 85,000 exceeds user 99th percentile"},
                    {"feature": "velocity_1h", "impact": 0.25, "description": "12 transactions in 60 minutes"},
                    {"feature": "device_score", "impact": 0.18, "description": "Device score 0.78 indicates unverified hardware"}
                ]
            }

    raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found.")
