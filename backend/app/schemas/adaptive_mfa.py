from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MFAFactorContribution(BaseModel):
    factor_name: str = Field(..., description="Factor label e.g., 'Transaction Anomaly', 'Hardware Attestation Failure'")
    risk_delta: float = Field(..., description="Additive point contribution to risk (+X points)")
    status: str = Field("OBSERVED", description="OBSERVED | MODEL_INFERRED | HARDWARE_ATTESTED | AI_INFERRED")
    evidence_summary: str = Field(..., description="Human and evaluator-readable rationale")
    provenance: str = Field("MODEL_INFERRED", description="Epistemic data origin")

class MFADecisionExplanation(BaseModel):
    case_id: str = Field(..., description="Associated Case Identifier")
    baseline_risk: float = Field(default=5.0, description="Base population transaction risk")
    factor_contributions: List[MFAFactorContribution] = Field(default_factory=list)
    total_calculated_risk: float = Field(..., description="Composite Risk Score (0 - 100)")
    required_auth_level: int = Field(..., ge=0, le=3, description="0: Passive, 1: Possession/OTP, 2: Passkey/WebAuthn, 3: Hardware Attestation")
    auth_level_label: str = Field(..., description="LEVEL_0_PASSIVE | LEVEL_1_POSSESSION_OTP | LEVEL_2_STRONG_PASSKEY | LEVEL_3_HARDWARE_ATTESTATION")
    required_action_title: str = Field(..., description="High-level required verification action")
    rationale: str = Field(..., description="Transparent explainability narrative")
    quantum_escalation_triggered: bool = Field(default=False)
    quantum_escalation_reason: Optional[str] = None
    provenance: str = "MODEL_INFERRED"

class AdaptiveMFAResponse(BaseModel):
    auth_session_id: str
    case_id: str
    user_id: str
    device_id: str
    timestamp_utc: str
    auth_level: int
    auth_level_label: str
    decision: str  # APPROVE | STEP_UP_REQUIRED | BLOCK
    explanation: MFADecisionExplanation
    challenge_payload: Optional[Dict[str, Any]] = None
    passkey_challenge: Optional[Dict[str, Any]] = None
    otp_masked_destination: Optional[str] = None
    status: str = "PENDING_VERIFICATION"  # VERIFIED | PENDING_VERIFICATION | FAILED

class MFAVerificationSubmission(BaseModel):
    auth_session_id: str
    case_id: str
    auth_type: str  # PASSIVE | OTP | PASSKEY | HARDWARE_CHALLENGE
    otp_code: Optional[str] = None
    passkey_signature: Optional[str] = None
    client_data_json: Optional[str] = None
    hardware_challenge_id: Optional[str] = None
    hardware_hmac_response: Optional[str] = None
    hardware_nonce: Optional[str] = None
    firmware_hash: Optional[str] = None
    monotonic_counter: Optional[int] = None
    timestamp_utc: Optional[str] = None

class MFAVerificationResult(BaseModel):
    auth_session_id: str
    case_id: str
    auth_type: str
    verified: bool
    final_decision: str  # APPROVE | STEP_UP | BLOCK
    post_verification_risk: float
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    provenance: str = "HARDWARE_ATTESTED"
