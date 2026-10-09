from typing import Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.copilot_service import copilot_service

router = APIRouter(prefix="/api", tags=["Q-Fraud Copilot AI Analyst"])

class CopilotQueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

@router.post("/copilot/chat", summary="Query Evidence-Grounded Q-Fraud Copilot Analyst")
async def chat_copilot(req: CopilotQueryRequest):
    """Chat with Q-Fraud Copilot AI Analyst grounded in SHAP, Graph, and Quantum evidence."""
    res = copilot_service.answer_query(req.query, req.context)
    return res
