from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class FileIntegrityMetadata(BaseModel):
    sha256_hash: Optional[str] = Field(default=None, description="Cryptographic SHA-256 hash of original image binary")
    detected_format: Optional[str] = Field(default=None, description="Actual file format detected from magic bytes (PNG, JPEG, WEBP, etc.)")
    mime_type: Optional[str] = Field(default=None, description="MIME type derived from magic bytes")
    file_size_bytes: Optional[int] = Field(default=None, description="Size of file in bytes")
    magic_bytes_valid: bool = Field(default=True, description="True if magic bytes match a supported image format")
    validation_error: Optional[str] = Field(default=None, description="Error reason if file validation failed")
    metadata_tamper_warning: Optional[str] = Field(default=None, description="EXIF or software editing tags indicating manipulation")

class VisualAssessment(BaseModel):
    ai_generation_likelihood: Optional[float] = Field(default=None, description="Probabilistic likelihood percentage (0-100) or null if indeterminate")
    ai_generation_assessment: str = Field(default="INCONCLUSIVE", description="LOW INDICATION | MODERATE INDICATION | HIGH INDICATION | INCONCLUSIVE | UNAVAILABLE")
    manipulation_level: str = Field(default="NONE_DETECTED", description="NONE_DETECTED | LOW | MODERATE | HIGH | UNAVAILABLE")
    manipulation_indicators: List[str] = Field(default_factory=list, description="Observed visual manipulation anomalies")
    image_integrity_score: Optional[float] = Field(default=None, description="Image structural integrity percentage or null")
    visual_consistency_score: Optional[float] = Field(default=None, description="Visual UI consistency percentage or null")
    text_consistency_score: Optional[float] = Field(default=None, description="Font and text alignment consistency percentage or null")
    ui_authenticity_score: Optional[float] = Field(default=None, description="Payment UI layout authenticity score or null")

class ExtractedPaymentFields(BaseModel):
    amount: Optional[float] = Field(default=None, description="Extracted transaction amount in INR")
    recipient_vpa: Optional[str] = Field(default=None, description="Extracted payee VPA / UPI ID")
    recipient_name: Optional[str] = Field(default=None, description="Extracted recipient display name")
    sender_name: Optional[str] = Field(default=None, description="Extracted payer display name")
    transaction_id: Optional[str] = Field(default=None, description="Extracted UPI Ref ID / Transaction Reference")
    timestamp_text: Optional[str] = Field(default=None, description="Extracted date & time string")
    merchant: Optional[str] = Field(default=None, description="Extracted merchant branding")
    payment_status: Optional[str] = Field(default=None, description="Extracted payment status (SUCCESS, PENDING, FAILED)")
    bank_or_app: Optional[str] = Field(default=None, description="Identified banking app or PSP interface")
    reference_number: Optional[str] = Field(default=None, description="Secondary reference number / UTR")

class EvidenceCheck(BaseModel):
    field: str = Field(..., description="Checked field name e.g. amount, recipient_vpa, merchant")
    extracted_value: Optional[Any] = Field(default=None, description="Value extracted from image / OCR")
    expected_or_qr_value: Optional[Any] = Field(default=None, description="Value from QR payload or declared context")
    result: str = Field(default="MATCH", description="MATCH | MISMATCH | UNAVAILABLE | SUSPICIOUS")
    impact: str = Field(default="LOW", description="LOW | MODERATE | HIGH | CRITICAL")
    description: str = Field(..., description="Explanation of match or mismatch")

class QRCrossCheck(BaseModel):
    status: str = Field(default="UNAVAILABLE", description="DECODED | NOT_FOUND | UNAVAILABLE")
    raw_qr_payload: Optional[str] = Field(default=None, description="Decoded QR URI / payload")
    recipient_comparison: str = Field(default="UNAVAILABLE", description="MATCH | MISMATCH | UNAVAILABLE")
    amount_comparison: str = Field(default="UNAVAILABLE", description="MATCH | MISMATCH | UNAVAILABLE")
    merchant_comparison: str = Field(default="UNAVAILABLE", description="MATCH | MISMATCH | UNAVAILABLE")
    system_derived_consistency_score: Optional[float] = Field(default=None, description="System-derived consistency percentage (0-100) or null")
    comparison_details: List[str] = Field(default_factory=list, description="Detailed consistency breakdown items")

class EvidenceVerificationRequest(BaseModel):
    image_base64: Optional[str] = Field(default=None, description="Base64-encoded image string (PNG, JPEG, WebP)")
    filename: Optional[str] = Field(default=None, description="Filename for MIME type determination")
    case_id: Optional[str] = Field(default=None, description="Associated investigation case ID")
    declared_amount: Optional[float] = Field(default=None, description="Declared or expected amount")
    declared_vpa: Optional[str] = Field(default=None, description="Declared recipient VPA")
    qr_payload_hint: Optional[str] = Field(default=None, description="Known QR payload to cross-verify against")

class EvidenceVerificationResponse(BaseModel):
    provider: str = Field(default="Gemini Multimodal", description="AI Provider identifier")
    analysis_status: str = Field(default="COMPLETED", description="COMPLETED | UNAVAILABLE | PARTIAL | ERROR | FALLBACK")
    status_message: Optional[str] = Field(default=None, description="Status detail message or error reason")
    file_integrity: FileIntegrityMetadata = Field(default_factory=FileIntegrityMetadata, description="File signature, magic bytes, SHA-256 hash")
    visual_assessment: VisualAssessment = Field(default_factory=VisualAssessment)
    extracted_fields: ExtractedPaymentFields = Field(default_factory=ExtractedPaymentFields)
    ocr_status: str = Field(default="UNAVAILABLE", description="EXTRACTED | NO_TEXT_DETECTED | UNAVAILABLE")
    ocr_text: Optional[str] = Field(default=None, description="Raw OCR text extracted from image")
    evidence_checks: List[EvidenceCheck] = Field(default_factory=list)
    qr_cross_check: QRCrossCheck = Field(default_factory=QRCrossCheck)
    overall_evidence_confidence: str = Field(default="HIGH", description="HIGH | MEDIUM | LOW | UNAVAILABLE")
    system_derived_consistency_score: Optional[float] = Field(default=None, description="Derived overall consistency score (0-100) or null")
    final_verdict: str = Field(default="INCONCLUSIVE", description="SUSPICIOUS | INCONCLUSIVE | NO_ISSUES_DETECTED")
    settlement_status: str = Field(
        default="UNVERIFIED_PENDING_SETTLEMENT",
        description="Visual inspection alone does not confirm bank settlement or fund reception"
    )
    settlement_disclaimer: str = Field(
        default="Screenshot / visual artifact inspection does not prove fund transfer or settlement. Confirmation requires banking gateway integration.",
        description="Settlement boundary disclaimer"
    )
    observations: List[str] = Field(default_factory=list, description="Observed evidence bullet points")
    limitations: List[str] = Field(default_factory=list, description="Forensic and environment limitations")
    provider_info: Dict[str, Any] = Field(default_factory=dict, description="Metadata regarding model version and execution mode")
