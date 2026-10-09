from typing import List, Optional
from fastapi import APIRouter, HTTPException, Path, Query
from backend.app.schemas.graph import (
    CaseGraphResponse, NetworkGraphResponse, MuleCluster
)
from backend.app.services.graph_service import graph_service

router = APIRouter(prefix="/api/graph", tags=["Fraud Graph & Relationship Intelligence"])

@router.get("/case/{case_id}", response_model=CaseGraphResponse, summary="Get Entity Subgraph for Investigation Case")
@router.get("/cases/{case_id}", response_model=CaseGraphResponse, include_in_schema=False)
async def get_case_graph(
    case_id: str = Path(..., description="Investigation Case ID or Transaction Identifier")
):
    """
    Returns the multi-hop entity relationship subgraph centered around the target case,
    including device links, recipient VPAs, domain infrastructure, and linked mule clusters.
    """
    case_graph = graph_service.get_case_graph(case_id)
    if not case_graph:
        raise HTTPException(status_code=404, detail=f"Case subgraph for '{case_id}' could not be resolved.")
    return case_graph

@router.get("/network", response_model=NetworkGraphResponse, summary="Get Full Macro Payment Network Graph")
async def get_network_graph():
    """
    Returns the comprehensive payment ecosystem topology with active mule rings,
    compromised clusters, and normal payment rails.
    """
    return graph_service.get_network_graph()

@router.get("/mule-rings", response_model=List[MuleCluster], summary="List Detected Mule Syndicate Rings")
async def list_mule_rings():
    """
    Returns detected multi-account mule syndicates with observed drain patterns and member nodes.
    """
    return graph_service.get_mule_clusters()
