from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional

from backend.app.schemas.adaptive_mfa import (
    AdaptiveMFAResponse, MFAVerificationSubmission, MFAVerificationResult
)
from backend.app.services.adaptive_mfa_service import adaptive_mfa_service

router = APIRouter(prefix="/api/v1/mfa", tags=["Adaptive Risk-Based Authentication"])

@router.post("/evaluate", response_model=AdaptiveMFAResponse)
def evaluate_mfa_policy(
    payload: Dict[str, Any] = Body(...)
):
    """
    Evaluates transaction risk & hardware signals to determine required MFA level (0-3).
    Returns additive risk breakdown and necessary challenge payload.
    """
    case_id = payload.get("case_id", "CASE-DEMO-001")
    user_id = payload.get("user_id", "USR-1001")
    device_id = payload.get("device_id", "QK-ESP32-7F3A")
    risk_score = float(payload.get("risk_score", 45.0))
    evidence = payload.get("evidence", [])
    risk_signals = payload.get("risk_signals", [])
    transaction_dna = payload.get("transaction_dna")
    quantum_analysis = payload.get("quantum_analysis")
    payload_integrity = payload.get("payload_integrity")
    device_trust = payload.get("device_trust_score")

    return adaptive_mfa_service.evaluate_adaptive_mfa(
        case_id=case_id,
        user_id=user_id,
        device_id=device_id,
        risk_score=risk_score,
        evidence_items=evidence,
        risk_signals=risk_signals,
        transaction_dna=transaction_dna,
        quantum_analysis=quantum_analysis,
        payload_integrity=payload_integrity,
        device_trust_score=device_trust
    )

@router.post("/verify", response_model=MFAVerificationResult)
def verify_mfa_response(
    submission: MFAVerificationSubmission
):
    """
    Verifies user OTP, Passkey, or ESP32-S3 Hardware Attestation challenge response.
    """
    return adaptive_mfa_service.verify_mfa_submission(submission)
