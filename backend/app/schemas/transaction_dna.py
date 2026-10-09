from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AmountBaseline(BaseModel):
    mean: float = 0.0
    std: float = 0.0
    median: float = 0.0
    min_amount: float = 0.0
    max_amount: float = 0.0
    p95: float = 0.0

class UserProfileDNA(BaseModel):
    user_id: str
    status: str = Field(default="INSUFFICIENT_HISTORY", description="ESTABLISHED | EMERGING | INSUFFICIENT_HISTORY")
    amount_baseline: AmountBaseline = Field(default_factory=AmountBaseline)
    typical_hour_range: List[int] = Field(default_factory=list)
    known_devices: List[str] = Field(default_factory=list)
    known_merchants: List[str] = Field(default_factory=list)
    known_locations: List[Dict[str, Any]] = Field(default_factory=list)
    velocity_baseline: float = 1.0
    profile_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    history_count: int = 0
    provenance: str = Field(default="OBSERVED", description="OBSERVED | INSUFFICIENT_HISTORY | MODEL_INFERRED")

class DNADeviationItem(BaseModel):
    dimension: str = Field(..., description="amount | time | device | merchant | location | velocity")
    display_name: str
    status: str = Field(..., description="NORMAL | DEVIATION | NOVEL | UNAVAILABLE")
    observed_value: Any
    baseline_value: Any
    deviation_score: float = Field(default=0.0, ge=0.0, le=1.0)
    severity: str = Field(default="LOW", description="LOW | MODERATE | HIGH | CRITICAL | NEUTRAL")
    details: str

class TransactionDNAResult(BaseModel):
    user_id: str
    evaluation_status: str = Field(default="INSUFFICIENT_HISTORY", description="EVALUATED | INSUFFICIENT_HISTORY | UNAVAILABLE")
    profile_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    history_count: int = 0
    dna_anomaly_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Normalized behavioral DNA deviation score 0-1")
    risk_impact: float = Field(default=0.0, ge=0.0, le=100.0, description="Point contribution to fraud risk")
    deviations: List[DNADeviationItem] = Field(default_factory=list)
    deviations_summary: List[str] = Field(default_factory=list)
    user_baseline: Optional[UserProfileDNA] = None
    provenance: str = Field(default="MODEL_INFERRED", description="OBSERVED | INSUFFICIENT_HISTORY | MODEL_INFERRED | HEURISTIC")
    summary: str = "Transaction DNA behavioral baseline assessment"
