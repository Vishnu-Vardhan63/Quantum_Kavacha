import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_attack_lab_generate_and_evaluate_qr_bytes():
    """Verify Attack Lab generates authentic PNG QR image bytes and evaluates via /api/check-payment."""
    # 1. Generate Phishing Lure simulated QR
    gen_res = client.post("/api/attack-lab/generate-qr", json={"scenario_type": "PHISHING_PAYMENT_LURE"})
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert gen_data["status"] == "GENERATED"
    assert "qr_base64" in gen_data
    assert len(gen_data["qr_base64"]) > 100
    assert gen_data["ground_truth_label"] == "SIMULATED_SUSPICIOUS"

    # 2. Submit PNG bytes directly to /api/check-payment under input_type="QR"
    check_res = client.post("/api/check-payment", json={
        "input_type": "QR",
        "payload": "",
        "image_base64": gen_data["qr_base64"],
        "allow_external_threat_lookup": False
    })
    assert check_res.status_code == 200
    check_data = check_res.json()
    assert check_data["analysis_status"] == "COMPLETED"
    # Verify QR image decoding succeeded
    qr_evidence = [e for e in check_data["evidence"] if e["field"] == "qr_raw_payload"]
    assert len(qr_evidence) > 0
    assert "payment-verification" in qr_evidence[0]["value"]
    # Check decision
    assert check_data["decision"] in ["BLOCK", "STEP_UP"]
    assert check_data["risk_score"] >= 50

def test_attack_lab_generate_and_evaluate_benign_qr():
    """Verify benign QR generation produces APPROVE with low risk score and no false positive."""
    gen_res = client.post("/api/attack-lab/generate-qr", json={"scenario_type": "BENIGN_BASELINE"})
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert gen_data["ground_truth_label"] == "SIMULATED_BENIGN"
    assert "qr_base64" in gen_data

    # Submit PNG bytes directly to /api/check-payment
    check_res = client.post("/api/check-payment", json={
        "input_type": "QR",
        "payload": "",
        "image_base64": gen_data["qr_base64"],
        "allow_external_threat_lookup": False
    })
    assert check_res.status_code == 200
    check_data = check_res.json()
    assert check_data["analysis_status"] == "COMPLETED"
    # Decoded QR should have UPI payee
    qr_evidence = [e for e in check_data["evidence"] if e["field"] == "qr_raw_payload"]
    assert len(qr_evidence) > 0
    assert "verified.store@icici" in qr_evidence[0]["value"]
    # Decision should be safe
    assert check_data["decision"] in ["APPROVE", "MONITOR"]
    assert check_data["risk_score"] <= 35
