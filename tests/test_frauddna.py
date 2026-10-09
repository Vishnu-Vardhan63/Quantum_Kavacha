import pytest
from backend.app.schemas.transaction import TransactionPayload
from backend.app.services.fraud_engine import fraud_engine
from backend.app.services.explanation_service import explanation_service
from backend.app.services.payment_forensics import payment_forensics_service
from backend.app.schemas.check_payment import CheckPaymentRequest

def test_frauddna_five_axes_structure():
    """Verify FraudDNA output contains all 5 primary dimensions with proper score and severity."""
    payload = TransactionPayload(
        txn_id="TXN-DNA-001",
        amount=65000.0,
        hour=2,
        velocity_1h=5,
        account_age_days=180,
        device_score=0.70,
        location_score=0.45,
        merchant_risk=0.50
    )
    res = fraud_engine.predict(payload)
    assert res.fraud_dna is not None
    assert "axes" in res.fraud_dna
    axes = res.fraud_dna["axes"]
    assert "amount_transaction" in axes
    assert "device" in axes
    assert "behavior" in axes
    assert "network_graph" in axes
    assert "quantum_complexity" in axes

    # Check that fingerprint list has 5 axes
    assert len(res.fraud_dna["fraud_dna_fingerprint"]) == 5
    assert res.fraud_dna["quality_check_passed"] is True

def test_frauddna_axis_inspection_details():
    """Verify every axis provides grounded risk drivers and mitigating factors with OBSERVED/INFERRED tags."""
    payload = TransactionPayload(
        txn_id="TXN-INSPECT-001",
        amount=85000.0,
        hour=23,
        velocity_1h=8,
        account_age_days=30,
        device_score=0.85,
        location_score=0.70,
        merchant_risk=0.80
    )
    res = fraud_engine.predict(payload)
    axes = res.fraud_dna["axes"]

    # Amount axis inspection
    amt_axis = axes["amount_transaction"]
    assert len(amt_axis["risk_drivers"]) > 0
    assert any(d["evidence_status"] in ["OBSERVED", "INFERRED"] for d in amt_axis["risk_drivers"])

    # Device axis inspection
    dev_axis = axes["device"]
    assert dev_axis["severity"] in ["HIGH", "CRITICAL"]
    assert len(dev_axis["risk_drivers"]) > 0

    # Behavior axis inspection
    beh_axis = axes["behavior"]
    assert beh_axis["severity"] in ["HIGH", "CRITICAL"]

def test_frauddna_dual_explanations():
    """Verify simple user explanation and technical analyst explanation are generated and consistent."""
    payload = TransactionPayload(
        txn_id="TXN-DUAL-001",
        amount=450.0,
        velocity_1h=1,
        account_age_days=365,
        device_score=0.1,
        location_score=0.1,
        merchant_risk=0.1
    )
    res = fraud_engine.predict(payload)
    summary = res.fraud_dna.get("explanation_summary", {})
    assert summary is not None
    assert "simple_explanation" in summary
    assert "technical_explanation" in summary
    assert "decision_rationale" in summary
    assert "safe" in summary["simple_explanation"].lower() or "approve" in summary["decision_rationale"].lower()

def test_frauddna_evidence_timeline():
    """Verify chronological evidence timeline is populated with valid categories and status tags."""
    payload = TransactionPayload(
        txn_id="TXN-TIME-001",
        amount=12000.0,
        velocity_1h=2,
        device_score=0.2,
        location_score=0.2,
        merchant_risk=0.2
    )
    res = fraud_engine.predict(payload)
    timeline = res.fraud_dna.get("evidence_timeline", [])
    assert len(timeline) >= 5
    events = [e["event"] for e in timeline]
    assert any("Payment Case Initialized" in ev for ev in events)
    assert any("Adaptive Decision Generated" in ev for ev in events)
    assert all(e["status"] in ["OBSERVED", "INFERRED", "UNAVAILABLE", "CONSISTENT", "INCONSISTENT"] for e in timeline)

def test_frauddna_limitations_panel():
    """Verify unverified external intelligence sources are explicitly cataloged in limitations."""
    payload = TransactionPayload(
        txn_id="TXN-LIMITS-001",
        amount=1500.0,
        velocity_1h=1,
        device_score=0.1,
        location_score=0.1,
        merchant_risk=0.1
    )
    res = fraud_engine.predict(payload)
    limits = res.fraud_dna.get("limitations", [])
    assert len(limits) > 0
    assert any("SIM-swap" in l or "VPA" in l or "Quantum" in l for l in limits)

def test_frauddna_copilot_context_payload():
    """Verify explanation_service.get_copilot_context outputs structured, grounded payload."""
    payload = TransactionPayload(
        txn_id="TXN-COPILOT-001",
        amount=75000.0,
        velocity_1h=7,
        device_score=0.8,
        location_score=0.6,
        merchant_risk=0.7
    )
    res = fraud_engine.predict(payload)
    copilot_ctx = explanation_service.get_copilot_context(res.model_dump())
    assert copilot_ctx["case_id"] == "TXN-COPILOT-001"
    assert "axes_summary" in copilot_ctx
    assert "simple_explanation" in copilot_ctx
    assert "technical_explanation" in copilot_ctx
    assert len(copilot_ctx["axes_summary"]) == 5

def test_frauddna_artifact_grounding():
    """Verify multi-modal forensic artifact signals propagate into appropriate FraudDNA axes."""
    req = CheckPaymentRequest(
        input_type="LINK",
        payload="https://secure-upi-paytm-verify-refund.xyz/pay?user=USR-9901&am=25000"
    )
    res = payment_forensics_service.analyze_payment(req)
    assert res.fraud_dna is not None
    axes = res.fraud_dna["axes"]
    net_axis = axes["network_graph"]
    assert net_axis["severity"] in ["HIGH", "CRITICAL"]
    assert any("Brand Lookalike" in d["title"] or "Domain" in d["title"] for d in net_axis["risk_drivers"])

def test_frauddna_quantum_honesty():
    """Verify quantum complexity axis does NOT claim quantum supremacy or unjustified advantage."""
    payload = TransactionPayload(
        txn_id="TXN-QUANT-001",
        amount=1000.0,
        velocity_1h=1,
        device_score=0.1,
        location_score=0.1,
        merchant_risk=0.1
    )
    res = fraud_engine.predict(payload)
    q_axis = res.fraud_dna["axes"]["quantum_complexity"]
    assert q_axis["severity"] == "NOT_ESCALATED"
    assert "Classical" in q_axis["primary_driver"] or "Standby" in q_axis["primary_driver"]
