from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class GraphNode(BaseModel):
    id: str = Field(..., description="Unique entity identifier (e.g. USR-9901, fakecare@ybl)")
    type: str = Field(..., description="Entity type: TRANSACTION | USER | DEVICE | RECIPIENT | NETWORK_DOMAIN | IP | MULE_HUB | MERCHANT")
    label: str = Field(..., description="Human-readable node label")
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Calibrated risk score (0-100)")
    risk_level: str = Field(default="LEGIT", description="LEGIT | MODERATE | SUSPICIOUS | HIGH RISK")
    status: str = Field(default="OBSERVED", description="OBSERVED | INFERRED | KNOWN_SAFE | ESCALATED")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Domain-specific attributes")
    cluster_id: Optional[str] = Field(default=None, description="Mule ring or cluster ID if affiliated")
    is_case_anchor: bool = Field(default=False, description="True if this node represents the investigated case anchor")
    pos_3d: Optional[List[float]] = Field(default=None, description="Initial 3D coordinates [x, y, z]")

class GraphEdge(BaseModel):
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    relationship: str = Field(..., description="Relationship type: INITIATED_BY | ACCESSED_VIA | ROUTED_TO | HOSTED_ON | MULE_TRANSFER | SHARED_HARDWARE | RESOLVES_TO")
    risk_weight: float = Field(default=0.5, ge=0.0, le=1.0, description="Relative risk weight of connection")
    evidence_source: str = Field(default="TELEMETRY", description="Source of relationship evidence")
    status: str = Field(default="OBSERVED", description="OBSERVED | INFERRED")

class MuleCluster(BaseModel):
    cluster_id: str = Field(..., description="Cluster identifier (e.g. MULE-RING-01)")
    name: str = Field(..., description="Syndicate / cluster display name")
    risk_level: str = Field(default="CRITICAL", description="Risk level of ring")
    member_count: int = Field(default=0, description="Total nodes in cluster")
    total_volume: float = Field(default=0.0, description="Aggregate transaction amount INR")
    primary_mule_vpa: str = Field(..., description="Central aggregation VPA / Account")
    description: str = Field(..., description="Forensic description of cluster activity")
    patterns: List[str] = Field(default_factory=list, description="Observed fraud patterns")
    node_ids: List[str] = Field(default_factory=list, description="IDs of constituent nodes")

class CaseGraphResponse(BaseModel):
    case_id: str
    anchor_node_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    clusters: List[MuleCluster]
    summary: Dict[str, Any]

class NetworkGraphResponse(BaseModel):
    total_nodes: int
    total_edges: int
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    mule_clusters: List[MuleCluster]
    stats: Dict[str, Any]
