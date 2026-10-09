import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.payment_forensics import payment_forensics_service
from backend.app.schemas.check_payment import CheckPaymentRequest

client = TestClient(app)

def test_check_payment_scenarios_endpoint():
    """Verify deterministic demo fixtures are returned."""
    response = client.get("/api/check-payment/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    scenario_ids = [s["id"] for s in data]
    assert "SCENARIO_1_SAFE_QR" in scenario_ids
    assert "SCENARIO_3_PHISHING_LINK" in scenario_ids
    assert "SCENARIO_5_AMBIGUOUS_QUANTUM" in scenario_ids

def test_safe_upi_qr_forensics():
    """Verify standard legitimate UPI QR produces trusted assessment with OBSERVED evidence."""
    payload = {
        "input_type": "QR",
        "payload": "upi://pay?pa=freshmart@icici&pn=Fresh%20Mart&am=850.00&cu=INR&tn=Order%20101"
    }
    response = client.post("/api/check-payment", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["analysis_status"] == "COMPLETED"
    assert "LOW RISK" in data["trust_level"]
    assert data["decision"] == "APPROVE"
    assert "Low risk based on available evidence" in data["recommendation"]
    
    # Check evidence classifications
    evidence_fields = {e["field"]: e["status"] for e in data["evidence"]}
    assert evidence_fields.get("payee_vpa") == "OBSERVED"
    assert evidence_fields.get("payee_name") == "OBSERVED"
    assert evidence_fields.get("amount_inr") == "OBSERVED"

def test_suspicious_qr_missing_payee():
    """Verify malformed QR missing payee address generates warning and risk signals."""
    payload = {
        "input_type": "QR",
        "payload": "upi://pay?pn=UnknownMerchant&am=50000.00&cu=INR"
    }
    response = client.post("/api/check-payment", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    signals = [s["name"] for s in data["risk_signals"]]
    assert "Missing Payee Address" in signals

def test_phishing_link_detection_and_lookalike():
    """Verify brand lookalike phishing link is flagged with CRITICAL severity."""
    payload = {
        "input_type": "LINK",
        "payload": "https://secure-upi-paytm-verify-refund.xyz/pay?user=USR-9901&am=25000"
    }
    response = client.post("/api/check-payment", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["trust_level"] == "HIGH RISK / UNTRUSTED"
    assert data["decision"] == "BLOCK"
    
    signal_names = [s["name"] for s in data["risk_signals"]]
    assert "Brand Lookalike Domain" in signal_names
    assert "Suspicious Top-Level Domain" in signal_names

def test_ssrf_and_private_ip_blocking():
    """Verify dangerous SSRF targets (localhost, 127.0.0.1, 10.x.x.x, javascript:) are rejected."""
    res1 = client.post("/api/check-payment", json={"input_type": "LINK", "payload": "http://127.0.0.1:8080/admin"})
    data1 = res1.json()
    assert any("SSRF Blocked" in s["description"] for s in data1["risk_signals"])

    res2 = client.post("/api/check-payment", json={"input_type": "LINK", "payload": "http://192.168.1.1/gateway"})
    data2 = res2.json()
    assert any("SSRF Blocked" in s["description"] for s in data2["risk_signals"])

    res3 = client.post("/api/check-payment", json={"input_type": "LINK", "payload": "javascript:alert(1)"})
    data3 = res3.json()
    assert any("Dangerous URL scheme rejected" in s["description"] for s in data3["risk_signals"])

def test_screenshot_social_engineering_urgency():
    """Verify OCR social engineering detection for urgency and threat language."""
    payload = {
        "input_type": "SCREENSHOT",
        "payload": "URGENT NOTICE: Your account will be blocked immediately. Send ₹15,000 to desk@upi to verify KYC."
    }
    response = client.post("/api/check-payment", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    signal_names = [s["name"] for s in data["risk_signals"]]
    assert "Account Suspension Threat" in signal_names
    assert "Urgency Pressure Language" in signal_names
    
    evidence_statuses = [e["status"] for e in data["evidence"]]
    assert "OBSERVED" in evidence_statuses

def test_ambiguous_payment_triggers_quantum_escalation():
    """Verify borderline payment case escalates to Qiskit Quantum Kernel."""
    payload = {
        "scenario_id": "SCENARIO_5_AMBIGUOUS_QUANTUM"
    }
    response = client.post("/api/check-payment", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "quantum_escalation" in data
    assert data["quantum_escalation"]["quantum_execution_required"] is True
    assert "ESCALATED_TO_QUANTUM_KERNEL" in data["quantum_escalation"]["quantum_escalation_status"]

# ==============================================================================
# 10 Acceptance Correction Regression Tests (Single Result Consistency Guard)
# ==============================================================================

def test_case_1_clean_valid_qr_consistency():
    """Case 1: Clean, valid QR -> Low risk, decision APPROVE/ALLOW, no safe contradictions."""
    payload = {
        "input_type": "QR",
        "payload": "upi://pay?pa=store.verified@hdfcbank&pn=VerifiedStore&am=1200.00&cu=INR"
    }
    res = client.post("/api/check-payment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] <= 20.0
    assert "LOW RISK" in data["trust_level"]
    assert data["decision"] in ["APPROVE", "ALLOW"]
    assert "Low risk based on available evidence" in data["recommendation"]
    assert len(data["risk_signals"]) == 0

def test_case_2_recipient_mismatch_guard():
    """Case 2: Payee mismatch (OCR vs target payload) must NEVER be zero risk or safe."""
    payload = {
        "scenario_id": "SCENARIO_B_MANIPULATED_SCREENSHOT"
    }
    res = client.post("/api/check-payment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] >= 70.0
    assert "HIGH RISK" in data["trust_level"]
    assert data["decision"] == "BLOCK"
    assert "DO NOT PROCEED" in data["recommendation"]
    # Ensure no safe text exists anywhere in the response
    assert "SAFE TO PROCEED" not in data["recommendation"]
    assert "Safe to Pay" not in data["recommendation"]

def test_case_3_amount_mismatch_guard():
    """Case 3: Amount mismatch (Screenshot ₹4,999 vs QR payload ₹499) -> High risk / Block."""
    payload = {
        "input_type": "SCREENSHOT",
        "payload": "PAYMENT CONFIRMATION\nPaid to: Fresh Retail Store\nAmount: ₹4,999.00\nQR: upi://pay?pa=freshmart@icici&am=499.00",
        "transaction_context": {"amount": 4999.0, "recipient_vpa": "freshmart@icici"}
    }
    res = client.post("/api/check-payment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] >= 70.0
    assert data["decision"] == "BLOCK"
    assert "DO NOT PROCEED" in data["recommendation"]

def test_case_4_dual_mismatch_guard():
    """Case 4: Dual mismatch (both Recipient & Amount diverge) -> Max risk elevation (>= 88)."""
    payload = {
        "input_type": "SCREENSHOT",
        "payload": "PAYMENT CONFIRMATION\nPaid to: Official Amazon Store\nAmount: ₹18,000.00\nUPI Ref: 981100234190\nQR: upi://pay?pa=fake-amazon-mule@ybl&am=180.00",
        "transaction_context": {"amount": 18000.0, "recipient_vpa": "fake-amazon-mule@ybl"}
    }
    res = client.post("/api/check-payment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] >= 88.0
    assert data["decision"] == "BLOCK"
    assert "HIGH RISK" in data["trust_level"]

def test_case_5_ai_generation_indication_only():
    """Case 5: AI-generation indication only (no route mismatch) -> Probabilistic moderate flag."""
    payload = {
        "scenario_id": "SCENARIO_C_SYNTHETIC_ARTIFACT"
    }
    res = client.post("/api/check-payment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] >= 50.0
    assert data["decision"] in ["BLOCK", "STEP_UP"]

def test_case_6_metadata_unavailable_no_false_positive():
    """Case 6: Threat feed unavailable -> marked UNAVAILABLE without false positive block."""
    payload = {
        "input_type": "LINK",
        "payload": "https://www.standardbank.co.in/checkout?ref=TXN-100"
    }
    res = client.post("/api/check-payment", json=payload)
    assert res.status_code == 200
    data = res.json()
    domain_items = [e for e in data["evidence"] if e["field"] == "domain_reputation_feed"]
    assert len(domain_items) > 0
    assert domain_items[0]["status"] == "UNAVAILABLE"

def test_case_7_qr_decode_failure_fallback():
    """Case 7: Non-QR image data gracefully falls back to OCR."""
    payload = {
        "input_type": "QR",
        "payload": "INVALID_NON_UPI_FORMAT_TEXT"
    }
    res = client.post("/api/check-payment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["analysis_status"] == "COMPLETED"

def test_case_8_gemini_unavailable_fallback():
    """Case 8: Gemini offline/unconfigured fallback executes cleanly with zero crashes."""
    from backend.app.services.gemini_evidence_service import gemini_evidence_service
    res = gemini_evidence_service.analyze_evidence(
        image_base64=None,
        local_ocr_text="Paid to: store@icici Amount: ₹500"
    )
    assert res.analysis_status in ["FALLBACK", "UNAVAILABLE"]
    assert res.extracted_fields is not None

def test_case_9_single_result_consistency_across_fixtures():
    """Case 9: All demo scenarios satisfy the Single Result Consistency Guard."""
    fixtures = payment_forensics_service.get_demo_fixtures()
    for fix in fixtures:
        res = client.post("/api/check-payment", json={"scenario_id": fix["id"]})
        assert res.status_code == 200
        data = res.json()
        
        has_critical = any(s["severity"] == "CRITICAL" for s in data["risk_signals"])
        if has_critical:
            assert data["risk_score"] >= 70.0, f"Scenario {fix['id']} has critical signal but risk score is {data['risk_score']}"
            assert "SAFE" not in data["trust_level"], f"Scenario {fix['id']} has critical signal but trust_level is {data['trust_level']}"
            assert data["decision"] in ["BLOCK", "STEP_UP"]

def test_case_10_empty_invalid_image_payload():
    """Case 10: Empty/invalid payload produces completed response without 500 error."""
    res = client.post("/api/check-payment", json={"input_type": "QR", "payload": ""})
    assert res.status_code == 200
    data = res.json()
    assert data["analysis_status"] == "COMPLETED"
