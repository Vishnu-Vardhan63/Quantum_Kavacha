from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel

from backend.app.schemas.investigation import (
    InvestigationCase, InvestigationCaseSummary, AnalystNote,
    AnalystDecisionRequest, CaseCreateRequest, CaseAnalyzeRequest
)
from backend.app.schemas.attack_chain import AttackChainResponse
from backend.app.schemas.response import ResponseCenterData, ActionAuditEntry
from backend.app.services.investigation_service import investigation_service
from backend.app.services.attack_chain_service import attack_chain_service
from backend.app.services.response_service import response_service

router = APIRouter(prefix="/api/investigation", tags=["Investigation Center"])

class NoteCreateRequest(BaseModel):
    note_type: str = "OBSERVATION" # OBSERVATION | HYPOTHESIS | DECISION_RATIONALE | FOLLOW_UP
    content: str
    author: Optional[str] = "Lead SOC Analyst"

class AuditActionRequest(BaseModel):
    action_name: str
    actor: Optional[str] = "ANALYST"
    details: str

@router.get("/cases", response_model=List[InvestigationCaseSummary], summary="List & Search Investigation Cases")
async def list_cases(
    q: Optional[str] = Query(default=None, description="Search term for case ID, recipient, or user"),
    limit: int = Query(default=50, ge=1, le=200)
):
    """Returns indexed cases for the Investigation Center workspace."""
    return investigation_service.list_cases(search_query=q, limit=limit)

@router.get("/cases/{case_id}", response_model=InvestigationCase, summary="Get Full Unified Investigation Case")
async def get_case(case_id: str = Path(..., description="Unique Case or Transaction Identifier")):
    """Retrieves full case details including summary, FraudDNA, evidence provenance, entities, and decision history."""
    case_obj = investigation_service.get_case(case_id)
    if not case_obj:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found in active store.")
    return case_obj

@router.get("/cases/{case_id}/attack-chain", response_model=AttackChainResponse, summary="Get Temporal Attack Chain Reconstruction")
async def get_attack_chain(case_id: str = Path(..., description="Unique Case Identifier")):
    """Reconstructs chronological attack chain story with provenance, breakpoints, and first warning indicators."""
    chain = attack_chain_service.reconstruct_attack_chain(case_id)
    if not chain:
        raise HTTPException(status_code=404, detail=f"Attack chain reconstruction unavailable for case '{case_id}'.")
    return chain

@router.get("/cases/{case_id}/response", response_model=ResponseCenterData, summary="Get Response Center Recommendations & Playbook")
async def get_case_response(case_id: str = Path(..., description="Unique Case Identifier")):
    """Retrieves evidence-grounded response recommendations, action cards, guided playbook, and evidence package."""
    case_obj = investigation_service.get_case(case_id)
    if not case_obj:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found.")
    return response_service.generate_response_center_data(case_obj)

@router.post("/cases/{case_id}/notes", response_model=AnalystNote, summary="Add Analyst Note to Case")
async def add_note(
    case_id: str = Path(...),
    req: NoteCreateRequest = ...
):
    """Appends an analyst-authored investigation note without mixing into machine evidence."""
    note = investigation_service.add_analyst_note(
        case_id=case_id,
        note_type=req.note_type,
        content=req.content,
        author=req.author or "Lead SOC Analyst"
    )
    if not note:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    
    # Also record in audit trail
    response_service.record_audit_action(
        case_id=case_id,
        action_name=f"Analyst Note Added ({req.note_type})",
        actor=req.author or "Lead SOC Analyst",
        details=req.content[:120] + ("..." if len(req.content) > 120 else "")
    )
    return note

@router.post("/cases/{case_id}/decision", response_model=InvestigationCase, summary="Submit Human Analyst Review Decision")
@router.post("/cases/{case_id}/analyst-decision", response_model=InvestigationCase, summary="Submit Human Analyst Review Decision (Alias)")
async def update_decision(
    case_id: str = Path(...),
    req: AnalystDecisionRequest = ...
):
    """Records human investigator decision and rationale separately from system assessment."""
    updated = investigation_service.update_analyst_decision(case_id=case_id, req=req)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    
    # Also record in audit trail
    response_service.record_audit_action(
        case_id=case_id,
        action_name=f"Analyst Decision: {req.analyst_action}",
        actor=req.author or "Lead SOC Analyst",
        details=req.rationale
    )
    return updated

@router.post("/cases/{case_id}/actions", response_model=ActionAuditEntry, summary="Record Response Action to Audit Trail")
async def record_case_action(
    case_id: str = Path(...),
    req: AuditActionRequest = ...
):
    """Logs an explicit user or analyst response action in the case audit trail."""
    case_obj = investigation_service.get_case(case_id)
    if not case_obj:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return response_service.record_audit_action(
        case_id=case_id,
        action_name=req.action_name,
        actor=req.actor or "ANALYST",
        details=req.details
    )

@router.get("/cases/{case_id}/report", summary="Get 11-Section Forensic Case Report Dossier")
async def get_case_report(case_id: str = Path(...)):
    """Exports structured 11-section forensic case dossier without exposing raw credentials or internal secrets."""
    case_obj = investigation_service.get_case(case_id)
    if not case_obj:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    
    # Record report export action in audit trail
    response_service.record_audit_action(
        case_id=case_id,
        action_name="Incident Evidence Dossier Exported",
        actor="ANALYST",
        details="Generated 11-section forensic report with evidence provenance."
    )
    return response_service.generate_forensic_report(case_obj)

@router.get("/cases/{case_id}/export", summary="Export Clean SOC Investigation Dossier Report")
async def export_case_report(case_id: str = Path(...)):
    """Exports structured case dossier without exposing raw credentials or internal secrets."""
    dossier = investigation_service.export_case_report(case_id)
    if not dossier:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return dossier

@router.post("/cases", response_model=InvestigationCase, summary="Create New Investigation Case Directly from Evidence")
async def create_case(req: CaseCreateRequest):
    """Directly creates and indexes a unified investigation case from uploaded file, QR, screenshot, URL, or context."""
    try:
        return investigation_service.create_case_from_evidence(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Case creation error: {str(e)}")

@router.post("/cases/{case_id}/analyze", response_model=InvestigationCase, summary="Re-Analyze or Augment Case Evidence")
async def analyze_case(
    case_id: str = Path(...),
    req: CaseAnalyzeRequest = ...
):
    """Re-executes analyzers on case evidence without duplicating records."""
    updated = investigation_service.retry_or_analyze_case(case_id, req)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return updated

@router.get("/cases/{case_id}/audit-verify", summary="Verify Tamper-Evident SHA-256 Audit Chain")
async def verify_audit_chain(case_id: str = Path(...)):
    """Cryptographically verifies every block in the case's SHA-256 audit chain from genesis to head."""
    res = investigation_service.verify_case_audit_chain(case_id)
    if not res.get("is_valid") and "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.post("/reset", summary="Reset Investigation Case Store to Deterministic Demo State")
async def reset_cases():
    """Resets the active case store to clean initial deterministic evaluation fixtures."""
    return investigation_service.reset_demo_cases()
