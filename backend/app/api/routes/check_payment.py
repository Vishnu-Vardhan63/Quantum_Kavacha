from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from backend.app.schemas.check_payment import CheckPaymentRequest, CheckPaymentResponse
from backend.app.services.payment_forensics import payment_forensics_service

router = APIRouter(prefix="/api", tags=["Check a Payment — Forensics"])

@router.post("/check-payment", response_model=CheckPaymentResponse, summary="Analyze Multi-Modal Digital Payment Artifact")
async def check_payment(req: CheckPaymentRequest):
    """
    Executes multi-modal digital payment forensics:
    - Decodes QR payloads & validates UPI parameters
    - Extracts OCR text & flags social engineering threats
    - Statically evaluates payment links with strict SSRF protection
    - Classifies evidence into OBSERVED, INFERRED, UNAVAILABLE
    - Fuses forensic indicators with hybrid ML & Quantum Escalation engine
    """
    try:
        res = payment_forensics_service.analyze_payment(req)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment forensics analysis error: {str(e)}")

@router.get("/check-payment/scenarios", summary="List Deterministic Payment Check Scenarios")
async def list_scenarios():
    """Returns predefined deterministic scenarios for 1-click judging and testing."""
    return payment_forensics_service.get_demo_fixtures()
