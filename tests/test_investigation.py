import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.investigation_service import investigation_service

client = TestClient(app)

def test_seeded_case_retrieval():
    """Verify default seeded cases are accessible with full structure."""
    res = client.get("/api/investigation/cases/QF-20261007-49910")
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "QF-20261007-49910"
    assert data["risk"]["risk_score"] == 92.4
    assert data["risk"]["decision"] == "BLOCK"
    assert data["status"] in ["ACTION_RECOMMENDED", "UNDER_REVIEW", "RESOLVED"]
    assert "summary" in data
    assert "what_happened" in data["summary"]
    assert "fraud_dna" in data
    assert "AMOUNT_TRANSACTION" in data["fraud_dna"]["axes"]
    assert len(data["entities"]) >= 3
    assert data["scorecard"]["evidence_quality"] == "HIGH"
    assert data["scorecard"]["external_intelligence"] == "UNAVAILABLE (No active external feeds)"

def test_check_payment_creates_investigation_case():
    """Test that evaluating a payment in Check a Payment automatically indexes a case."""
    payload = {
        "input_type": "LINK",
        "payload": "https://secure-hdfc-kyc.top/verify?user=8801",
        "scenario_id": "SCENARIO_2_SUSPICIOUS_PHISHING",
        "transaction_context": {
            "amount": 50000.0,
            "velocity_1h": 8,
            "device_score": 0.75,
            "user_id": "USR-8801"
        }
    }
    res = client.post("/api/check-payment", json=payload)
    assert res.status_code == 200
    check_data = res.json()
    case_id = check_data["case_id"]

    # Verify case can now be retrieved in Investigation Center
    inv_res = client.get(f"/api/investigation/cases/{case_id}")
    assert inv_res.status_code == 200
    inv_data = inv_res.json()

    # Verify authoritative risk consistency
    assert inv_data["case_id"] == case_id
    assert inv_data["risk"]["risk_score"] == check_data["risk_score"]
    assert inv_data["risk"]["decision"] == check_data["decision"]
    assert inv_data["risk"]["confidence"] == check_data["confidence"]
    assert len(inv_data["evidence"]) == len(check_data["evidence"])

def test_list_and_search_cases():
    """Verify case listing and text searching across IDs and entities."""
    res = client.get("/api/investigation/cases")
    assert res.status_code == 200
    cases = res.json()
    assert len(cases) >= 1

    # Search for known seeded case
    search_res = client.get("/api/investigation/cases?q=49910")
    assert search_res.status_code == 200
    search_cases = search_res.json()
    assert len(search_cases) >= 1
    assert any(c["case_id"] == "QF-20261007-49910" for c in search_cases)

def test_evidence_provenance_retention():
    """Verify evidence items retain OBSERVED, INFERRED, UNAVAILABLE statuses in investigation."""
    res = client.get("/api/investigation/cases/QF-20261007-49910")
    assert res.status_code == 200
    ev_list = res.json()["evidence"]
    statuses = {e["status"] for e in ev_list}
    assert "OBSERVED" in statuses
    assert "INFERRED" in statuses
    assert "UNAVAILABLE" in statuses

def test_add_analyst_note_separation():
    """Verify human analyst notes are stored separately from machine evidence."""
    case_id = "QF-20261007-49910"
    note_payload = {
        "note_type": "HYPOTHESIS",
        "content": "Suspected phishing kit reusing template from last week campaign.",
        "author": "Forensic Lead"
    }
    res = client.post(f"/api/investigation/cases/{case_id}/notes", json=note_payload)
    assert res.status_code == 200
    note_data = res.json()
    assert note_data["note_type"] == "HYPOTHESIS"
    assert "Suspected phishing kit" in note_data["content"]
    assert note_data["author"] == "Forensic Lead"

    # Verify note is present in case
    case_res = client.get(f"/api/investigation/cases/{case_id}")
    notes = case_res.json()["analyst_notes"]
    assert any("Suspected phishing kit" in n["content"] for n in notes)

def test_analyst_decision_update():
    """Verify human analyst review updates decision record separately from system assessment."""
    case_id = "QF-20261007-49910"
    dec_payload = {
        "analyst_action": "CONFIRM_RECOMMENDATION",
        "rationale": "Forensic analysis confirms domain spoofing and malicious payee intent.",
        "author": "Senior Analyst"
    }
    res = client.post(f"/api/investigation/cases/{case_id}/decision", json=dec_payload)
    assert res.status_code == 200
    updated_case = res.json()
    dec_rec = updated_case["decision_history"]
    assert dec_rec["system_decision"] == "BLOCK"
    assert dec_rec["analyst_review_status"] == "CONFIRMED"
    assert dec_rec["analyst_action"] == "CONFIRM_RECOMMENDATION"
    assert dec_rec["analyst_rationale"] == "Forensic analysis confirms domain spoofing and malicious payee intent."

def test_export_case_dossier():
    """Verify investigation case export produces clean, sanitized dossier."""
    case_id = "QF-20261007-49910"
    res = client.get(f"/api/investigation/cases/{case_id}/export")
    assert res.status_code == 200
    dossier = res.json()
    assert dossier["case_id"] == case_id
    assert "report_meta" in dossier
    assert "system_assessment" in dossier
    assert "fraud_dna" in dossier
    assert "entities" in dossier
    assert "limitations_and_disclosures" in dossier
    # Verify no raw secrets or passwords in export
    dossier_str = str(dossier).lower()
    assert "password" not in dossier_str
    assert "secret_key" not in dossier_str
