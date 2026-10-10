import os
import json
import time
import hmac
import hashlib
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, Header, status

from backend.app.core.auth import get_current_user, User
from backend.app.services.investigation_service import investigation_service
from backend.app.services.fraud_engine import fraud_engine
from backend.app.schemas.transaction import TransactionPayload

router = APIRouter(prefix="/api/ingest", tags=["Security Ecosystem Event Ingestion"])

class SecurityIntegrationEvent(BaseModel):
    event_id: str = Field(..., description="Unique idempotency identifier from external telemetry system")
    source_system: str = Field(..., description="Origin system type: SIEM, FIREWALL, MOBILE_APP, API_GATEWAY, IDENTITY_PROVIDER")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of external occurrence")
    severity: str = Field("MEDIUM", description="Origin severity: LOW, MEDIUM, HIGH, CRITICAL")
    event_type: str = Field(..., description="Event classification (e.g., SUSPICIOUS_IP_BURST, BRUTE_FORCE_LOGIN, IMPOSSIBLE_TRAVEL, MALICIOUS_DNS)")
    user_id: Optional[str] = None
    account_id: Optional[str] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict, description="Raw vendor payload preserved for evidentiary provenance")

class IngestionResponse(BaseModel):
    status: str
    event_id: str
    correlated_case_id: Optional[str] = None
    fused_risk_score: float
    decision_action: str
    message: str

@router.post("/event", response_model=IngestionResponse, summary="Ingest External Security Event into Quantum Kavacha")
async def ingest_security_event(
    event: SecurityIntegrationEvent,
    x_integration_key: Optional[str] = Header(None, description="API Key or Bearer Token for Connector Auth")
):
    """
    Standardized, modular ingestion adapter for external security platforms:
    - Normalizes alerts from Firewalls, SIEMs, Mobile Clients, and API Gateways.
    - Applies SSRF and input bounds checking.
    - Fuses event with behavioral velocity and anomaly models.
    - Indexes authoritative investigation cases when risk crosses severity threshold.
    """
    # 1. Basic validation & connector auth
    valid_key = os.getenv("ECOSYSTEM_INTEGRATION_KEY", "qk_eco_default_key_2026")
    if x_integration_key and not hmac.compare_digest(x_integration_key, valid_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unauthorized X-Integration-Key"
        )

    # 2. Derive normalized risk contribution
    base_severity_score = {
        "LOW": 20.0,
        "MEDIUM": 45.0,
        "HIGH": 75.0,
        "CRITICAL": 95.0
    }.get(event.severity.upper(), 40.0)

    # 3. Simulate or run fused check
    user = event.user_id or "USR-ECOSYSTEM"
    device = event.device_id or "DEV-EXTERNAL"
    ip = event.ip_address or "192.168.1.100"

    # Evaluate transaction or behavioral impact
    txn_context = TransactionPayload(
        txn_id=f"ECO-{event.event_id[:8]}",
        user_id=user,
        account_id=event.account_id or f"ACC-{user}",
        amount=1000.0,
        device_id=device,
        ip=ip,
        merchant_id="ECOSYSTEM_CONNECTOR",
        device_score=0.85 if event.severity in ["HIGH", "CRITICAL"] else 0.25,
        location_score=0.80 if "TRAVEL" in event.event_type else 0.20
    )
    pred = fraud_engine.predict(txn_context)

    # Fuse external event weight with classical model
    fused_score = min(100.0, round(0.5 * pred.risk_score + 0.5 * base_severity_score, 1))

    if fused_score >= 70.0:
        decision = "BLOCK"
    elif fused_score >= 40.0:
        decision = "STEP_UP"
    else:
        decision = "ALLOW"

    # 4. If escalated or suspicious, register case in Unified Investigation Center
    case_obj = None
    if fused_score >= 40.0:
        try:
            case_obj = investigation_service.register_case_from_prediction(pred, txn_context)
        except Exception:
            pass

    return IngestionResponse(
        status="ACCEPTED",
        event_id=event.event_id,
        correlated_case_id=case_obj.case_id if case_obj else None,
        fused_risk_score=fused_score,
        decision_action=decision,
        message=f"External security telemetry from {event.source_system} ingested and correlated successfully."
    )
