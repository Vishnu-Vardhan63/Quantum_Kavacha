from typing import List, Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from models.drift.drift_monitor import drift_monitor
from backend.app.services.simulation_service import simulation_service

router = APIRouter(prefix="/api", tags=["Concept Drift"])

@router.get("/drift", summary="Evaluate Real-Time Concept Drift Status")
async def get_drift_status():
    """Retrieve concept drift metrics, PSI feature shifts, and retraining triggers."""
    records = []
    for item in simulation_service.buffer:
        records.append(item["transaction"])
    
    drift_result = drift_monitor.evaluate_drift(records)
    return drift_result
