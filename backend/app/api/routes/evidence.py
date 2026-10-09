import base64
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from backend.app.schemas.evidence import (
    EvidenceVerificationRequest, EvidenceVerificationResponse
)
from backend.app.services.gemini_evidence_service import gemini_evidence_service
from backend.app.services.payment_forensics import payment_forensics_service

router = APIRouter(prefix="/api/evidence", tags=["Gemini Multimodal Evidence Verification"])

@router.post("/analyze", response_model=EvidenceVerificationResponse, summary="Analyze Multimodal Payment Evidence with Gemini")
def analyze_evidence_json(req: EvidenceVerificationRequest):
    """
    Analyzes uploaded payment evidence (Screenshot, QR Image, Receipt):
    - File integrity, magic bytes, SHA-256 hash
    - Visual authenticity & synthetic/AI-generation assessment
    - Manipulation indicators (font mismatches, duplicated elements, alignment flaws)
    - Semantic field extraction (amount, recipient VPA, txn ID, bank/app)
    - Cross-verification against RapidOCR and QR payload
    """
    try:
        decoded_qr = None
        if req.image_base64:
            decoded_text, err = payment_forensics_service.decode_qr_image(req.image_base64)
            if decoded_text:
                decoded_qr = payment_forensics_service.parse_upi_payload(decoded_text)
                decoded_qr["raw_text"] = decoded_text

        return gemini_evidence_service.analyze_evidence(
            image_base64=req.image_base64,
            filename=req.filename,
            case_id=req.case_id,
            declared_amount=req.declared_amount,
            declared_vpa=req.declared_vpa,
            qr_payload_hint=req.qr_payload_hint,
            decoded_qr_data=decoded_qr
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evidence verification error: {str(e)}")

@router.post("/verify", response_model=EvidenceVerificationResponse, summary="Verify Multimodal Payment Evidence")
def verify_evidence_json(req: EvidenceVerificationRequest):
    """
    Direct endpoint for evidence verification matching /api/evidence/verify contract.
    Identical logic to /api/evidence/analyze for backward and forward compatibility.
    """
    return analyze_evidence_json(req)

@router.post("/upload", response_model=EvidenceVerificationResponse, summary="Upload & Analyze Payment Evidence Multipart")
async def upload_evidence(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(default=None),
    declared_amount: Optional[float] = Form(default=None),
    declared_vpa: Optional[str] = Form(default=None)
):
    """Multipart file upload endpoint for direct forensic evidence analysis."""
    try:
        contents = await file.read()
        b64_str = base64.b64encode(contents).decode("utf-8")
        
        decoded_text, err = payment_forensics_service.decode_qr_image(b64_str)
        decoded_qr = None
        if decoded_text:
            decoded_qr = payment_forensics_service.parse_upi_payload(decoded_text)
            decoded_qr["raw_text"] = decoded_text

        return gemini_evidence_service.analyze_evidence(
            image_base64=b64_str,
            filename=file.filename,
            case_id=case_id,
            declared_amount=declared_amount,
            declared_vpa=declared_vpa,
            decoded_qr_data=decoded_qr
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evidence upload verification failed: {str(e)}")
