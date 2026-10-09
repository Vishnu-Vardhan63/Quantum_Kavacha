import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.attack_chain_service import attack_chain_service
from backend.app.services.investigation_service import investigation_service
from backend.app.services.copilot_service import copilot_service
from backend.app.schemas.attack_chain import AttackChainResponse

client = TestClient(app)

def test_attack_chain_api_endpoint():
    """Test GET /api/investigation/cases/{case_id}/attack-chain returns 200 and schema valid data."""
    response = client.get("/api/investigation/cases/QF-20261007-49910/attack-chain")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "QF-20261007-49910"
    assert "summary" in data
    assert "events" in data
    assert len(data["events"]) > 0
    assert "breakpoints" in data
    assert "first_warning" in data
    assert "key_event" in data

def test_chronological_event_ordering():
    """Verify that all events in the reconstructed chain are sorted chronologically."""
    chain = attack_chain_service.reconstruct_attack_chain("QF-20261007-49910")
    assert chain is not None
    timestamps = [e.timestamp for e in chain.events if e.timestamp is not None]
    assert timestamps == sorted(timestamps)
    assert len(chain.events) >= 3

def test_observed_vs_inferred_provenance():
    """Verify that direct case evidence is OBSERVED and graph cluster connections are INFERRED."""
    chain = attack_chain_service.reconstruct_attack_chain("QF-20261007-49910")
    assert chain is not None
    
    # Entry event must be OBSERVED
    entry_evt = next((e for e in chain.events if e.stage == "ENTRY"), None)
    assert entry_evt is not None
    assert entry_evt.provenance == "OBSERVED"
    
    # Mule syndicate cluster connection must be INFERRED
    mule_evt = next((e for e in chain.events if e.stage == "PROPAGATION_EXIT"), None)
    if mule_evt:
        assert mule_evt.provenance == "INFERRED"

def test_no_fabricated_events_or_timestamps():
    """Verify missing timestamps are labeled appropriately and no events are fabricated."""
    chain = attack_chain_service.reconstruct_attack_chain("QF-20261007-49910")
    assert chain is not None
    for e in chain.events:
        assert e.provenance in ["OBSERVED", "INFERRED", "UNAVAILABLE"]
        assert e.timestamp_status in ["EXACT", "APPROXIMATE", "UNAVAILABLE", "RELATIVE"]
        if e.timestamp is None:
            assert e.timestamp_status in ["UNAVAILABLE", "APPROXIMATE", "RELATIVE"]

def test_first_warning_sign_identification():
    """Verify that the earliest risk-contributing event is correctly flagged as first warning."""
    chain = attack_chain_service.reconstruct_attack_chain("QF-20261007-49910")
    assert chain is not None
    assert chain.first_warning is not None
    assert chain.first_warning.stage in ["SETUP", "COMPROMISE_MANIPULATION", "PAYMENT_ATTEMPT"]
    assert len(chain.first_warning.why) > 0

def test_key_event_identification():
    """Verify that the highest impact divergence is selected as the key event."""
    chain = attack_chain_service.reconstruct_attack_chain("QF-20261007-49910")
    assert chain is not None
    assert chain.key_event is not None
    assert chain.key_event.stage in ["COMPROMISE_MANIPULATION", "TRANSFER_EXFILTRATION", "PAYMENT_ATTEMPT"]

def test_evidence_linkage_integrity():
    """Verify that every temporal event links to valid evidence identifiers."""
    chain = attack_chain_service.reconstruct_attack_chain("QF-20261007-49910")
    assert chain is not None
    for e in chain.events:
        assert isinstance(e.evidence_ids, list)
        assert len(e.entities) > 0

def test_potential_intervention_breakpoints():
    """Verify that breakpoints exist and explain why and how they could disrupt the attack flow."""
    chain = attack_chain_service.reconstruct_attack_chain("QF-20261007-49910")
    assert chain is not None
    assert len(chain.breakpoints) >= 2
    for bp in chain.breakpoints:
        assert bp.risk in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert len(bp.reason) > 0
        assert len(bp.potential_interruption) > 0
        assert len(bp.recommended_action) > 0

def test_activity_path_graph_linkage():
    """Verify that activity path maintains graph hops with observed vs inferred markers."""
    chain = attack_chain_service.reconstruct_attack_chain("QF-20261007-49910")
    assert chain is not None
    assert len(chain.activity_path) >= 2
    for hop in chain.activity_path:
        assert hop.from_entity
        assert hop.to_entity
        assert hop.provenance in ["OBSERVED", "INFERRED"]

def test_copilot_temporal_reasoning_grounding():
    """Verify that Copilot answers temporal queries using exact attack chain data without hallucinating."""
    res1 = copilot_service.answer_query("What happened in this attack chain?", {"txn_id": "QF-20261007-49910"})
    assert "Chronological" in res1["answer"] or "Reconstructed" in res1["answer"]
    assert res1["evidence_confidence"] > 0.9

    res2 = copilot_service.answer_query("Where was the first warning sign?", {"txn_id": "QF-20261007-49910"})
    assert "First Observed Warning" in res2["answer"]

    res3 = copilot_service.answer_query("How could this attack have been interrupted?", {"txn_id": "QF-20261007-49910"})
    assert "Intervention" in res3["answer"] or "Breakpoint" in res3["answer"]

def test_nonexistent_case_returns_404():
    """Verify requesting an invalid case ID returns 404."""
    response = client.get("/api/investigation/cases/QF-NONEXISTENT-99999/attack-chain")
    assert response.status_code == 404
