from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.transaction import (
    SignalSummaryItem, FeatureContribution, CrossSignalConsistency,
    ModelDisagreementInfo, FusionResult, CounterfactualResult
)
from backend.app.schemas.evidence import EvidenceVerificationResponse

class CrossValidationItem(BaseModel):
    field: str = Field(..., description="amount | merchant | vpa | reference_id | timestamp")
    status: str = Field(..., description="MATCH | MISMATCH | UNAVAILABLE")
    ocr_value: Optional[Any] = None
    qr_value: Optional[Any] = None
    context_value: Optional[Any] = None
    severity: str = Field(default="NEUTRAL", description="NEUTRAL | LOW | MODERATE | HIGH | CRITICAL")
    details: Optional[str] = None

class CrossValidationResult(BaseModel):
    status: str = Field(default="UNAVAILABLE", description="MATCH | MISMATCH | UNAVAILABLE")
    overall_match: bool = True
    items: Dict[str, CrossValidationItem] = Field(default_factory=dict)
    mismatches_count: int = 0
    matches_count: int = 0
    unavailable_count: int = 0
    summary: str = "Cross-validation pending"

class EvidenceItem(BaseModel):
    category: str = Field(..., description="Category: IDENTIFIER | AMOUNT | RECIPIENT | NETWORK | CONTENT | BEHAVIOR")
    field: str = Field(..., description="Field name e.g., payee_vpa, domain_structure")
    value: Any = Field(..., description="Extracted value")
    status: str = Field(..., description="OBSERVED | INFERRED | UNAVAILABLE")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction or inference confidence")
    source: str = Field(default="DIRECT_EXTRACTION", description="Extraction source: QR_PAYLOAD | OCR_TEXT | STATIC_URL_PARSER | SYSTEM")

class RiskSignal(BaseModel):
    name: str
    severity: str # LOW | MODERATE | HIGH | CRITICAL
    status: str # OBSERVED | INFERRED | UNAVAILABLE
    description: str
    interpretation: str

class CheckPaymentRequest(BaseModel):
    input_type: str = Field(default="QR", description="QR | SCREENSHOT | LINK | TRANSACTION | FILE")
    payload: Optional[str] = Field(default=None, description="Decoded URI, raw text, or URL")
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded PNG/JPEG image or file payload")
    filename: Optional[str] = Field(default=None, description="Original filename for validation")
    scenario_id: Optional[str] = Field(default=None, description="Optional preset scenario ID")
    transaction_context: Optional[Dict[str, Any]] = Field(default=None, description="Optional transaction context")
    allow_external_threat_lookup: bool = Field(default=True, description="Allow external reputation queries (VirusTotal, WHOIS, DNS)")
    external_file_submission_consent: bool = Field(default=False, description="Explicit consent for external file binary submission")

class CheckPaymentResponse(BaseModel):
    case_id: str
    input_type: str
    evidence_type: str = Field(default="PAYMENT_ARTIFACT", description="GENERAL_DOCUMENT | INVOICE | PAYMENT_RECEIPT | BANK_STATEMENT | QR_CODE | URL_LINK | UNKNOWN")
    transaction_detected: bool = Field(default=True, description="Whether actual payment or transaction evidence was detected")
    final_verdict: str = Field(default="SAFE", description="SAFE | SUSPICIOUS | MALICIOUS | INCONCLUSIVE | NOT_APPLICABLE")
    payment_status: str = Field(default="VERIFIED", description="NOT_APPLICABLE | PENDING_REVIEW | SUSPECTED_FRAUD | VERIFIED")
    timestamp: float
    analysis_status: str # COMPLETED | REVIEW_REQUIRED | INVALID_INPUT
    trust_level: str # LOW RISK BASED ON AVAILABLE EVIDENCE | SUSPICIOUS / CAUTION | HIGH RISK / UNTRUSTED
    risk_score: float # 0 - 100
    confidence: float # 0.0 - 1.0 (decoupled epistemic confidence)
    decision: str # APPROVE | MONITOR | STEP_UP | HOLD | BLOCK
    recommendation: str # Action recommendation for user/analyst
    evidence: List[EvidenceItem]
    risk_signals: List[RiskSignal]
    signal_summary: Optional[List[SignalSummaryItem]] = Field(default_factory=list)
    cross_signal_consistency: Optional[CrossSignalConsistency] = None
    cross_validation: Optional[CrossValidationResult] = None
    fusion_result: Optional[FusionResult] = None
    model_disagreement: Optional[ModelDisagreementInfo] = None
    feature_contributions: Optional[Dict[str, Any]] = None
    mitigation_factors: Optional[List[str]] = Field(default_factory=list)
    warnings: List[str]
    quantum_escalation: Dict[str, Any]
    fraud_dna: Optional[Dict[str, Any]] = None
    counterfactuals: Optional[List[Dict[str, Any]]] = None
    counterfactual_result: Optional[CounterfactualResult] = None
    timings: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    evidence_verification: Optional[EvidenceVerificationResponse] = None
    threat_intelligence: Optional[Dict[str, Any]] = Field(default=None, description="Domain intelligence, DNS, TLS, WHOIS, and VirusTotal results")
    payload_integrity: Optional[Dict[str, Any]] = Field(default=None, description="Correlated payment payload integrity assessment")
    transaction_dna: Optional[Dict[str, Any]] = Field(default=None, description="Behavioral baseline profile and deviations")

