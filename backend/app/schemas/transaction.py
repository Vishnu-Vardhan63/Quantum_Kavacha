from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class StageTiming(BaseModel):
    stage: str
    latency_ms: float

class SignalSummaryItem(BaseModel):
    category: str = Field(..., description="ARTIFACT | BEHAVIORAL | IDENTITY_DEVICE | RECIPIENT | GRAPH | MODEL_ENSEMBLE | QUANTUM")
    name: str
    status: str = Field(..., description="OBSERVED | INFERRED | UNAVAILABLE")
    severity: str = Field(default="NEUTRAL", description="LOW | MODERATE | HIGH | CRITICAL | NEUTRAL")
    description: str
    score_contribution: float = Field(default=0.0, description="Estimated point impact on risk score")

class FeatureContribution(BaseModel):
    feature: str
    contribution: float
    direction: str = Field(..., description="INCREASES_RISK | REDUCES_RISK")
    description: str

class CrossSignalConsistency(BaseModel):
    status: str = Field(..., description="CONSISTENT | INCONSISTENT | UNAVAILABLE")
    score: float = Field(default=1.0, ge=0.0, le=1.0, description="Consistency confidence score 0.0 to 1.0")
    conflicts: List[str] = Field(default_factory=list)
    details: List[Dict[str, Any]] = Field(default_factory=list)

class ModelDisagreementInfo(BaseModel):
    disagreement_score: float = Field(..., ge=0.0, le=1.0, description="Standard deviation or spread across models")
    interpretation: str = Field(..., description="HIGH_AGREEMENT | MODERATE_DISPERSION | HIGH_DISAGREEMENT")
    model_spread: Dict[str, float] = Field(default_factory=dict)
    epistemic_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Model uncertainty level (0=certain, 1=uncertain)")

class FusionContribution(BaseModel):
    source: str = Field(..., description="Evidence dimension key e.g. transaction_ml, qr_consistency, ocr_consistency, etc.")
    display_name: str = Field(..., description="Human-readable transparent label")
    raw_score: float = Field(..., ge=0.0, le=1.0, description="Normalized dimension score 0.0 to 1.0")
    weight: float = Field(..., ge=0.0, le=1.0, description="Fusion weighting factor")
    weighted_impact: float = Field(..., description="Score points contributed to base risk")
    provenance: str = Field(default="MODEL_INFERRED", description="OBSERVED | MODEL_INFERRED | AI_INFERRED | HEURISTIC | UNAVAILABLE | SYSTEM_GENERATED")
    description: str

class FusionResult(BaseModel):
    base_score: float = Field(..., ge=0.0, le=100.0, description="Base multi-criteria score before deterministic guards")
    evidence_contributions: List[FusionContribution] = Field(default_factory=list)
    deterministic_adjustments: List[Dict[str, Any]] = Field(default_factory=list)
    final_score: float = Field(..., ge=0.0, le=100.0, description="Final authoritative score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Epistemic confidence")
    triggered_rules: List[str] = Field(default_factory=list)
    provenance: str = Field(default="SYSTEM_GENERATED", description="OBSERVED | MODEL_INFERRED | AI_INFERRED | HEURISTIC | UNAVAILABLE | SYSTEM_GENERATED")
    summary: str

class CounterfactualItem(BaseModel):
    change: str = Field(..., description="Controllable parameter mutated")
    display_name: str
    feature: str
    original_value: Any
    counterfactual_value: Any
    new_score: float = Field(..., ge=0.0, le=100.0)
    delta: float = Field(..., description="Score change (negative means risk reduction)")
    resulting_status: str = Field(default="APPROVED", description="APPROVED | REVIEW | BLOCK")
    rationale: str
    provenance: str = Field(default="MODEL_INFERRED", description="OBSERVED | MODEL_INFERRED | AI_INFERRED | HEURISTIC | UNAVAILABLE | SYSTEM_GENERATED")

class CounterfactualResult(BaseModel):
    baseline_score: float
    counterfactuals: List[CounterfactualItem] = Field(default_factory=list)
    primary_remediation: Optional[str] = None

class FraudDNAAxisDetail(BaseModel):
    axis_id: str
    display_name: str
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    severity: str = Field(default="LOW", description="LOW | MODERATE | HIGH | CRITICAL | ESCALATED | NOT_ESCALATED | UNAVAILABLE")
    status: str = Field(default="OBSERVED", description="OBSERVED | INFERRED | UNAVAILABLE")
    primary_driver: str
    risk_drivers: List[Dict[str, Any]] = Field(default_factory=list)
    mitigating_factors: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: str

class EvidenceTimelineEvent(BaseModel):
    time_offset_ms: int = Field(default=0)
    event: str
    status: str = Field(default="OBSERVED", description="OBSERVED | INFERRED | UNAVAILABLE")
    category: str = Field(default="SYSTEM", description="ARTIFACT | IDENTITY | CONSISTENCY | ENSEMBLE | QUANTUM | DECISION")
    details: str

class ExplanationSummary(BaseModel):
    simple_explanation: str
    technical_explanation: str
    decision_rationale: str
    confidence_interpretation: str

class FraudDNAStructured(BaseModel):
    fraud_dna_fingerprint: List[Dict[str, Any]] = Field(default_factory=list)
    axes: Dict[str, FraudDNAAxisDetail] = Field(default_factory=dict)
    primary_driver: str = Field(default="Unknown")
    quantum_similarity_level: str = Field(default="LOW ANOMALY")
    evidence_timeline: List[EvidenceTimelineEvent] = Field(default_factory=list)
    explanation_summary: Optional[ExplanationSummary] = None
    limitations: List[str] = Field(default_factory=list)
    quality_check_passed: bool = Field(default=True)

class TransactionPayload(BaseModel):
    txn_id: Optional[str] = Field(default="TXN-TEMP", description="Transaction ID")
    user_id: Optional[str] = Field(default="USR-1001", description="User ID")
    account_id: Optional[str] = Field(default="ACC-1001", description="Account ID")
    device_id: Optional[str] = Field(default="DEV-2001", description="Device ID")
    ip: Optional[str] = Field(default="192.168.1.1", description="IP Address")
    merchant_id: Optional[str] = Field(default="MERCH-501", description="Merchant ID")
    lat: Optional[float] = Field(default=19.0760, description="Latitude")
    lon: Optional[float] = Field(default=72.8777, description="Longitude")
    amount: float = Field(..., gt=0.0, description="Amount in currency (e.g. INR)")
    hour: int = Field(default=12, ge=0, le=23, description="Hour of day (0-23)")
    velocity_1h: int = Field(default=1, ge=0, description="Transactions count in last hour")
    account_age_days: int = Field(default=365, ge=0, description="Account age in days")
    device_score: float = Field(default=0.1, ge=0.0, le=1.0, description="Device anomaly score")
    location_score: float = Field(default=0.1, ge=0.0, le=1.0, description="Location anomaly score")
    merchant_risk: float = Field(default=0.1, ge=0.0, le=1.0, description="Merchant risk score")
    forensic_signals: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional multi-modal forensic signals from QR/Screenshot/Link")
    artifact_context: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata extracted from payment artifact")

class PredictionResponse(BaseModel):
    txn_id: str
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Combined risk score 0-100")
    risk_level: str = Field(..., description="NORMAL, SUSPICIOUS, or HIGH RISK")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Epistemic confidence decoupled from risk")
    decision: str = Field(..., description="APPROVE, MONITOR, STEP_UP, HOLD, or BLOCK")
    recommendation: Optional[str] = Field(default=None, description="Actionable recommendation for user or analyst")
    model_scores: Dict[str, float]
    model_disagreement: Optional[ModelDisagreementInfo] = None
    cross_signal_consistency: Optional[CrossSignalConsistency] = None
    signal_summary: Optional[List[SignalSummaryItem]] = Field(default_factory=list)
    top_positive_contributors: Optional[List[FeatureContribution]] = Field(default_factory=list)
    top_negative_contributors: Optional[List[FeatureContribution]] = Field(default_factory=list)
    mitigation_factors: Optional[List[str]] = Field(default_factory=list)
    risk_factors: List[str]
    quantum_execution_mode: str = Field(default="SIMULATION", description="SIMULATION, NOISY SIMULATION, or HARDWARE")
    quantum_active: bool
    quantum_escalation: Optional[Dict[str, Any]] = None
    velocity_details: Optional[Dict[str, Any]] = None
    fraud_dna: Optional[Dict[str, Any]] = None
    counterfactuals: Optional[List[Dict[str, Any]]] = None
    counterfactual_result: Optional[CounterfactualResult] = None
    fusion_result: Optional[FusionResult] = None
    transaction_dna: Optional[Dict[str, Any]] = None
    pre_fraud_warning: Optional[Dict[str, Any]] = None
    timings: List[StageTiming]
