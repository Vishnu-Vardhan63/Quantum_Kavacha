from typing import Dict, Any, Optional, List
from fastapi import APIRouter
from pydantic import BaseModel, Field
from backend.app.services.copilot_service import copilot_service

router = APIRouter(prefix="/api", tags=["Q-Fraud Copilot AI Analyst"])

class CopilotQueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class CopilotQueryResponse(BaseModel):
    query: str
    answer: str
    grounded_sources: List[str] = Field(default_factory=list)
    evidence_confidence: float = 0.95
    provider: str = "DETERMINISTIC_FALLBACK"
    execution_mode: str = "RULE_BASED_FALLBACK"

@router.post("/copilot/chat", response_model=CopilotQueryResponse, summary="Query Evidence-Grounded Q-Fraud Copilot Analyst")
def chat_copilot(req: CopilotQueryRequest):
    """Chat with Q-Fraud Copilot AI Analyst grounded in SHAP, Graph, and Quantum evidence."""
    res = copilot_service.answer_query(req.query, req.context)
    return res
