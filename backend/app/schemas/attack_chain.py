from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TemporalEvent(BaseModel):
    event_id: str = Field(..., description="Unique event ID, e.g. EVT-01")
    case_id: str
    timestamp: Optional[float] = None
    timestamp_formatted: str = Field(..., description="E.g. '09:41:12' or 'Time unavailable' or 'Approximate'")
    timestamp_status: str = Field(default="EXACT", description="EXACT | APPROXIMATE | UNAVAILABLE | RELATIVE")
    stage: str = Field(..., description="ENTRY | SETUP | COMPROMISE_MANIPULATION | PAYMENT_ATTEMPT | VELOCITY_BURST | TRANSFER_EXFILTRATION | PROPAGATION_EXIT | NOT_ESTABLISHED")
    event_type: str = Field(..., description="Machine event type code")
    title: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="Detailed description of what happened")
    entities: List[str] = Field(default_factory=list, description="Associated entity identifiers")
    evidence_ids: List[str] = Field(default_factory=list, description="Fields or IDs of supporting evidence")
    provenance: str = Field(..., description="OBSERVED | INFERRED | UNAVAILABLE")
    confidence: str = Field(default="HIGH", description="HIGH | MEDIUM | LOW")
    impact: str = Field(default="MEDIUM", description="CRITICAL | HIGH | MEDIUM | LOW | INFORMATIONAL")
    source: str = Field(..., description="Origin of event telemetry")
    why_it_matters: str = Field(default="", description="Forensic significance explanation")
    technical_details: Dict[str, Any] = Field(default_factory=dict)

class AttackChainBreakpoint(BaseModel):
    breakpoint_id: str
    stage: str
    title: str
    risk: str = Field(default="HIGH", description="CRITICAL | HIGH | MEDIUM | LOW")
    reason: str
    recommended_action: str
    evidence_ids: List[str] = Field(default_factory=list)
    potential_interruption: str = Field(..., description="Explanation of how this intervention could disrupt the attack flow")

class AttackChainSummary(BaseModel):
    events_count: int
    observed_count: int
    inferred_count: int
    unavailable_count: int
    time_span: str = Field(default="Relative sequence only")
    entities_involved: int
    reconstruction_confidence: str = Field(default="HIGH", description="HIGH | MEDIUM | LOW (Refers to quality of reconstruction)")
    human_readable_story: str

class FirstWarningSign(BaseModel):
    event_id: str
    title: str
    timestamp_formatted: str
    why: str
    stage: str

class KeyEvent(BaseModel):
    event_id: str
    title: str
    timestamp_formatted: str
    why: str
    stage: str

class LastKnownActivity(BaseModel):
    event_id: Optional[str] = None
    title: str
    timestamp_formatted: str
    stage: str

class ActivityPathHop(BaseModel):
    from_entity: str
    to_entity: str
    relationship: str
    provenance: str = Field(default="OBSERVED", description="OBSERVED | INFERRED")
    notes: Optional[str] = None

class AttackChainResponse(BaseModel):
    case_id: str
    case_status: str
    risk_score: float
    decision: str
    summary: AttackChainSummary
    events: List[TemporalEvent]
    breakpoints: List[AttackChainBreakpoint]
    first_warning: Optional[FirstWarningSign] = None
    key_event: Optional[KeyEvent] = None
    last_known_event: Optional[LastKnownActivity] = None
    activity_path: List[ActivityPathHop] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
