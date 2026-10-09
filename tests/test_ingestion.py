import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_security_event_ingestion_valid():
    payload = {
        "event_id": "EVT-SIEM-99210-XYZ",
        "source_system": "SIEM",
        "timestamp": 1773000000.0,
        "severity": "HIGH",
        "event_type": "SUSPICIOUS_IP_BURST",
        "user_id": "USR-EXT-8801",
        "account_id": "ACC-EXT-8801",
        "ip_address": "198.51.100.45",
        "device_id": "DEV-EXT-ALPHA",
        "raw_payload": {"rule_name": "Consecutive_Failed_Logins", "count": 14}
    }

    res = client.post("/api/ingest/event", json=payload, headers={"X-Integration-Key": "qk_eco_default_key_2026"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ACCEPTED"
    assert data["event_id"] == "EVT-SIEM-99210-XYZ"
    assert data["fused_risk_score"] >= 40.0
    assert data["decision_action"] in ["STEP_UP", "BLOCK"]

def test_security_event_ingestion_unauthorized_key():
    payload = {
        "event_id": "EVT-FW-001",
        "source_system": "FIREWALL",
        "severity": "CRITICAL",
        "event_type": "MALICIOUS_C2_TRAFFIC"
    }
    res = client.post("/api/ingest/event", json=payload, headers={"X-Integration-Key": "wrong_invalid_key"})
    assert res.status_code == 401
    assert "Invalid or unauthorized" in res.json()["detail"]
