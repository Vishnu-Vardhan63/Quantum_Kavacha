import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class EntityDetail(BaseModel):
    entity_id: str = Field(..., description="Tokenized or extracted entity identifier")
    entity_type: str = Field(..., description="USER | ACCOUNT | DEVICE | TRANSACTION | RECIPIENT | MERCHANT | PAYMENT_ARTIFACT | NETWORK_DOMAIN")
    name: str = Field(..., description="Descriptive entity name")
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    status: str = Field(default="OBSERVED", description="OBSERVED | INFERRED | UNAVAILABLE")
    attributes: Dict[str, Any] = Field(default_factory=dict)
    connected_count: int = Field(default=1)

class AnalystNote(BaseModel):
    note_id: str
    timestamp: float
    author: str = Field(default="Lead SOC Analyst")
    note_type: str = Field(default="OBSERVATION", description="OBSERVATION | HYPOTHESIS | DECISION_RATIONALE | FOLLOW_UP")
    content: str

class AnalystDecisionRequest(BaseModel):
    analyst_action: str = Field(..., description="CONFIRM_RECOMMENDATION | OVERRIDE_STEP_UP | OVERRIDE_APPROVE | ESCALATE_TO_SENIOR | DISMISS_FALSE_POSITIVE")
    rationale: str
    author: Optional[str] = "Lead SOC Analyst"

class CaseDecisionRecord(BaseModel):
    system_decision: str
    system_recommendation: str
    system_risk_score: float
    analyst_review_status: str = Field(default="PENDING", description="PENDING | CONFIRMED | MODIFIED | RESOLVED")
    analyst_action: Optional[str] = None
    analyst_rationale: Optional[str] = None
    updated_at: float

class InvestigationScorecard(BaseModel):
    evidence_quality: str = Field(default="HIGH", description="HIGH | MEDIUM | LOW")
    model_confidence: str = Field(default="HIGH", description="HIGH | MEDIUM | LOW")
    entity_context: str = Field(default="AVAILABLE", description="AVAILABLE | PARTIAL | LIMITED")
    graph_context: str = Field(default="READY", description="READY | PENDING")
    external_intelligence: str = Field(default="UNAVAILABLE (No active external feeds)", description="Explicit boundary disclosure")

class RelatedCase(BaseModel):
    case_id: str
    relationship_type: str = Field(..., description="SAME_DEVICE | SAME_RECIPIENT | SAME_USER | SIMILAR_ARTIFACT")
    risk_score: float
    decision: str
    timestamp: float
    shared_attribute: str

class CaseSummary(BaseModel):
    what_happened: str
    why_suspicious: str
    what_should_happen_next: str
    primary_risk_drivers: List[str] = Field(default_factory=list)
    mitigating_factors: List[str] = Field(default_factory=list)

class InvestigationCaseSummary(BaseModel):
    case_id: str
    status: str
    source: str
    created_at: float
    amount: float
    risk_score: float
    decision: str
    quantum_escalated: bool
    recipient: str
    device_id: str

class InvestigationCase(BaseModel):
    case_id: str
    status: str = Field(default="UNDER_REVIEW", description="NEW | ANALYZING | UNDER_REVIEW | ESCALATED | ACTION_RECOMMENDED | RESOLVED")
    created_at: float
    updated_at: float
    source: str = Field(default="CHECK_PAYMENT", description="CHECK_PAYMENT | API_PREDICT | SIMULATION_FEED")
    summary: CaseSummary
    risk: Dict[str, Any]
    quantum_escalation: Dict[str, Any]
    fraud_dna: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    entities: List[EntityDetail]
    related_cases: List[RelatedCase] = Field(default_factory=list)
    scorecard: InvestigationScorecard
    model_analysis: Dict[str, Any]
    counterfactuals: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    analyst_notes: List[AnalystNote] = Field(default_factory=list)
    decision_history: CaseDecisionRecord
    pre_fraud_warning: Optional[Dict[str, Any]] = None
    audit_chain: List[Dict[str, Any]] = Field(default_factory=list)

class AuditChainEntry(BaseModel):
    index: int = Field(default=0)
    timestamp: float = Field(default_factory=time.time)
    event: str
    actor: str = "SYSTEM"
    details: str
    prev_hash: str = "0" * 64
    entry_hash: str

class CaseCreateRequest(BaseModel):
    title: Optional[str] = None
    input_type: str = Field(default="AUTO", description="AUTO | QR | SCREENSHOT | LINK | FILE | TRANSACTION")
    payload: Optional[str] = Field(default=None, description="Decoded URI, raw text, or URL")
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded image or file data")
    filename: Optional[str] = Field(default=None, description="Uploaded file name")
    transaction_context: Optional[Dict[str, Any]] = Field(default=None, description="Associated transaction context")
    allow_external_threat_lookup: bool = True
    external_file_submission_consent: bool = False
    analyst_note: Optional[str] = None

class CaseAnalyzeRequest(BaseModel):
    re_run_all: bool = False
    analyzer_subset: Optional[List[str]] = None
    additional_transaction_context: Optional[Dict[str, Any]] = None
