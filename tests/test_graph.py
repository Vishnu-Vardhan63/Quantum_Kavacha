import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.graph_service import graph_service

client = TestClient(app)

def test_get_case_graph_seeded_case():
    """Verify entity subgraph generation for the primary demo case QF-20261007-49910."""
    res = client.get("/api/graph/case/QF-20261007-49910")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == "QF-20261007-49910"
    assert data["anchor_node_id"] == "QF-20261007-49910"
    assert len(data["nodes"]) >= 5
    assert len(data["edges"]) >= 4

    # Check anchor node
    anchor = next(n for n in data["nodes"] if n["id"] == "QF-20261007-49910")
    assert anchor["type"] == "TRANSACTION"
    assert anchor["is_case_anchor"] is True
    assert anchor["risk_score"] > 80.0

    # Check connected entity types
    node_types = {n["type"] for n in data["nodes"]}
    assert "USER" in node_types
    assert "DEVICE" in node_types
    assert "RECIPIENT" in node_types
    assert "NETWORK_DOMAIN" in node_types

    # Check 2-hop mule aggregation hub
    assert any(n["type"] == "MULE_HUB" for n in data["nodes"])

    # Check summary
    summary = data["summary"]
    assert summary["total_nodes"] == len(data["nodes"])
    assert summary["high_risk_node_count"] >= 3

def test_get_network_graph():
    """Verify macro payment ecosystem graph endpoint."""
    res = client.get("/api/graph/network")
    assert res.status_code == 200
    data = res.json()

    assert data["total_nodes"] >= 10
    assert data["total_edges"] >= 8
    assert len(data["mule_clusters"]) >= 2
    assert "stats" in data
    assert data["stats"]["mule_rings_active"] >= 2

def test_list_mule_rings():
    """Verify list of identified mule syndicates."""
    res = client.get("/api/graph/mule-rings")
    assert res.status_code == 200
    clusters = res.json()

    assert isinstance(clusters, list)
    assert len(clusters) >= 2
    
    alpha = next(c for c in clusters if c["cluster_id"] == "MULE-RING-01")
    assert alpha["primary_mule_vpa"] == "fakecare@ybl"
    assert len(alpha["patterns"]) >= 2
    assert alpha["total_volume"] > 0

def test_dynamic_case_graph_generation():
    """Verify graph generation for a newly analyzed payment case."""
    # Analyze a new test payment payload
    test_payload = {
        "input_type": "LINK",
        "payload": "https://secure-bank-login.xyz/pay?upi=stealthmule@axis&pn=Axis%20Official&am=75000",
        "transaction_context": {
            "user_id": "USR-NEW-TEST",
            "device_id": "DEV-TEST-UNKNOWN",
            "hour": 2,
            "velocity_1h": 14,
            "device_score": 0.88,
            "location_score": 0.85,
            "merchant_risk": 0.90
        }
    }
    analyze_res = client.post("/api/check-payment", json=test_payload)
    assert analyze_res.status_code == 200
    case_id = analyze_res.json()["case_id"]

    # Now retrieve graph for this new case
    graph_res = client.get(f"/api/graph/case/{case_id}")
    assert graph_res.status_code == 200
    graph_data = graph_res.json()

    assert graph_data["case_id"] == case_id
    assert any(n["id"] == case_id for n in graph_data["nodes"])
    # Check that new recipient and device entities appear in the graph
    node_ids = {n["id"] for n in graph_data["nodes"]}
    assert "USR-NEW-TEST" in node_ids
    assert "DEV-TEST-UNKNOWN" in node_ids
    assert "stealthmule@axis" in node_ids
