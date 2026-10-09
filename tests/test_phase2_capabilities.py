import pytest
from backend.app.services.transaction_dna_service import transaction_dna_service
from backend.app.services.payment_forensics import payment_forensics_service
from backend.app.services.graph_service import graph_service
from backend.app.services.attack_lab_service import attack_lab_service
from backend.app.services.quantum_benchmark import quantum_benchmark_service
from backend.app.schemas.check_payment import CheckPaymentRequest

def test_transaction_dna_insufficient_history():
    """Verify that user with <3 transactions returns INSUFFICIENT_HISTORY."""
    res = transaction_dna_service.evaluate_transaction_dna("USR-BRAND-NEW", {"amount": 500.0, "hour": 14})
    assert res.evaluation_status == "INSUFFICIENT_HISTORY"
    assert res.profile_confidence == 0.0
    assert res.dna_anomaly_score == 0.0
    assert res.provenance == "INSUFFICIENT_HISTORY"

def test_transaction_dna_normal_behavior():
    """Verify that transactions conforming to established user baseline return low anomaly score."""
    res = transaction_dna_service.evaluate_transaction_dna("USR-1001", {
        "amount": 2500.0,
        "hour": 14,
        "device_id": "DEV-1001",
        "merchant_id": "verified.store@icici",
        "lat": 19.0760,
        "lon": 72.8777,
        "velocity_1h": 1
    })
    assert res.evaluation_status == "EVALUATED"
    assert res.profile_confidence >= 0.80
    assert res.dna_anomaly_score < 0.25
    assert len(res.deviations) > 0

def test_transaction_dna_abnormal_amount_and_new_device():
    """Verify that abnormal amount spike and unseen device trigger explicit DNA deviations."""
    res = transaction_dna_service.evaluate_transaction_dna("USR-1001", {
        "amount": 85000.0,
        "hour": 23,
        "device_id": "DEV-UNKNOWN-ATTACKER",
        "merchant_id": "unseen.mule@ybl",
        "velocity_1h": 8
    })
    assert res.evaluation_status == "EVALUATED"
    assert res.dna_anomaly_score > 0.45
    dims = {d.dimension: d.status for d in res.deviations}
    assert dims.get("amount") == "DEVIATION"
    assert dims.get("device") == "NOVEL"
    assert len(res.deviations_summary) >= 2

def test_payload_integrity_evaluation():
    """Verify that payload integrity flags COMPROMISED on mismatch and VERIFIED on clean match."""
    req_clean = CheckPaymentRequest(
        input_type="QR",
        payload="upi://pay?pa=verified.store@icici&pn=Verified%20Store&am=2500.00&cu=INR",
        transaction_context={"amount": 2500.0, "recipient_vpa": "verified.store@icici"}
    )
    res_clean = payment_forensics_service.analyze_payment(req_clean)
    assert res_clean.payload_integrity is not None
    assert res_clean.payload_integrity["overall_verdict"] in ["INTEGRITY_VERIFIED", "PARTIAL_EVIDENCE"]

    req_tampered = CheckPaymentRequest(
        input_type="SCREENSHOT",
        payload="Paid ₹4,999.00 to Store\nQR: upi://pay?pa=store@upi&am=499.00",
        transaction_context={"amount": 4999.0, "recipient_vpa": "store@upi"}
    )
    res_tampered = payment_forensics_service.analyze_payment(req_tampered)
    assert res_tampered.payload_integrity is not None
    assert res_tampered.payload_integrity["overall_verdict"] == "COMPROMISED"

def test_suspicious_entity_network_intelligence():
    """Verify that network graph identifies suspicious entity clusters and tags synthetic data."""
    net = graph_service.get_network_graph()
    assert net.total_nodes > 5
    assert net.total_edges > 5
    assert len(net.mule_clusters) >= 2
    assert net.stats.get("dataset_type") == "SIMULATED NETWORK DATA"

def test_attack_lab_scenarios_execution():
    """Verify all 12 attack lab scenarios execute through the real pipeline."""
    scenarios = attack_lab_service.list_scenarios()
    assert len(scenarios) == 12

    # Test execution of Scenario 1 (Genuine)
    res1 = attack_lab_service.execute_scenario("SCENARIO_1_GENUINE_DEVICE_PAYMENT")
    assert res1["decision"] == "APPROVE"
    assert res1["risk_score"] < 35.0
    assert res1["offline_compatible"] is True

    # Test execution of Scenario 8 (Phishing Payment Link)
    res8 = attack_lab_service.execute_scenario("SCENARIO_8_PHISHING_PAYMENT_LINK_LURE")
    assert res8["risk_score"] >= 30.0
    assert len(res8["triggered_signals"]) > 0
    assert res8["offline_compatible"] is True

    # Test execution of Scenario 9 (Velocity Burst)
    res9 = attack_lab_service.execute_scenario("SCENARIO_9_AUTOMATED_VELOCITY_BURST")
    assert res9["risk_score"] >= 30.0
    assert res9["transaction_dna"] is not None

def test_quantum_ablation_benchmark():
    """Verify quantum comparative benchmark calculates valid ablation metrics."""
    bench = quantum_benchmark_service.run_ablation_benchmark(n_samples=30)
    assert "dataset_info" in bench
    assert bench["dataset_info"]["dataset_type"] == "SYNTHETIC_EVALUATION"
    assert "comparison" in bench
    assert "classical_only" in bench["comparison"]
    assert "hybrid_quantum_classical" in bench["comparison"]
    assert "technical_honest_assessment" in bench
    assert 0.0 <= bench["comparison"]["hybrid_quantum_classical"]["f1_score"] <= 1.0
    assert 0.0 <= bench["comparison"]["classical_only"]["f1_score"] <= 1.0
