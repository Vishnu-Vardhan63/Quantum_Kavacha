from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ResponseRecommendation(BaseModel):
    primary_action: str = Field(..., description="e.g. DO NOT PAY, REVIEW BEFORE PROCEEDING, PROCEED WITH NORMAL CAUTION, SECURE ACCOUNT")
    primary_action_code: str = Field(..., description="DO_NOT_PAY | REVIEW_BEFORE_PROCEEDING | PROCEED_WITH_CAUTION | SECURE_ACCOUNT")
    headline: str
    rationale: str
    risk_level: str = Field(..., description="LOW | MEDIUM | HIGH | CRITICAL")
    risk_score: float = Field(..., ge=0.0, le=100.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_level: str = Field(..., description="HIGH | MEDIUM | LOW")
    evidence_quality: str = Field(..., description="HIGH | MEDIUM | LOW")
    verification_recommendation: str = Field(..., description="NORMAL_VERIFICATION | STEP_UP_VERIFICATION | STRONG_VERIFICATION | DO_NOT_PROCEED")
    verification_rationale: str
    is_compromise_suspected: bool = Field(default=False)

class ActionCard(BaseModel):
    id: str
    title: str
    description: str
    action_type: str = Field(..., description="RECOMMENDED | USER_ACTION | SIMULATED | UNAVAILABLE | EXTERNAL_ACTION")
    status: str = Field(default="RECOMMENDED", description="RECOMMENDED | PENDING | COMPLETED | NOT_APPLICABLE")
    why: str
    evidence_grounding: List[str] = Field(default_factory=list)
    action_button_label: str
    action_url: Optional[str] = None
    is_simulated: bool = False
    disclaimer: Optional[str] = None

class PlaybookStep(BaseModel):
    step_number: int
    title: str
    instruction: str
    why: str
    evidence: str
    status: str = Field(default="ACTION_RECOMMENDED", description="ACTION_RECOMMENDED | PENDING | OPTIONAL | COMPLETED")
    actor: str = Field(default="USER", description="USER | ANALYST | EXTERNAL")

class EvidencePackageItem(BaseModel):
    field_name: str
    field_label: str
    value: Any
    provenance: str = Field(..., description="OBSERVED | INFERRED | UNAVAILABLE | DEMO / SYNTHETIC")
    notes: Optional[str] = None

class EvidencePackage(BaseModel):
    case_id: str
    generated_at: str
    items: List[EvidencePackageItem]
    summary_markdown: str
    raw_evidence_count: int
    observed_fields_count: int
    inferred_fields_count: int
    unavailable_fields_count: int
    unavailable_fields: List[str]

class ActionAuditEntry(BaseModel):
    entry_id: str
    timestamp: float
    timestamp_formatted: str
    action_name: str
    actor: str = Field(default="SYSTEM", description="SYSTEM | ANALYST | USER")
    details: str
    provenance: str = Field(default="OBSERVED", description="OBSERVED | SYSTEM_GENERATED")

class SimpleViewGuide(BaseModel):
    what_should_i_do: str
    primary_recommendation: str
    why_explanation: str
    what_to_do_now: List[str]
    what_to_avoid: List[str]
    when_to_seek_help: str
    checklist_status: str

class ResponseCenterData(BaseModel):
    case_id: str
    risk_score: float
    confidence: float
    evidence_quality: str
    recommendation: ResponseRecommendation
    action_cards: List[ActionCard]
    playbook: List[PlaybookStep]
    evidence_package: EvidencePackage
    audit_trail: List[ActionAuditEntry]
    analyst_decision: Optional[Dict[str, Any]] = None
    simple_view_guide: SimpleViewGuide
    limitations: List[str] = Field(default_factory=list)
    boundary_disclaimer: str = Field(
        default="Q-FraudShield provides risk recommendations based on available telemetry. It does not directly freeze external bank accounts or execute irreversible financial actions without authorized bank API integrations."
    )
