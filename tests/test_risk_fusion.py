import pytest
from backend.app.schemas.transaction import TransactionPayload
from backend.app.services.fraud_engine import fraud_engine
from backend.app.services.payment_forensics import payment_forensics_service
from backend.app.schemas.check_payment import CheckPaymentRequest

def test_safe_payment_risk_fusion():
    """Test safe transaction fusion: low risk, high confidence, APPROVE decision, consistent signals."""
    payload = TransactionPayload(
        txn_id="TXN-SAFE-001",
        user_id="USR-SAFE",
        account_id="ACC-001",
        device_id="DEV-TRUSTED",
        amount=450.0,
        hour=14,
        velocity_1h=1,
        account_age_days=300,
        device_score=0.08,
        location_score=0.05,
        merchant_risk=0.10
    )
    res = fraud_engine.predict(payload)
    assert res.risk_score < 40.0
    assert res.risk_level == "NORMAL"
    assert res.decision == "APPROVE"
    assert res.confidence >= 0.70
    assert len(res.signal_summary) > 0
    assert res.model_disagreement is not None
    assert res.model_disagreement.interpretation in ["HIGH_AGREEMENT", "MODERATE_DISPERSION"]

def test_artifact_only_risk_fusion():
    """Test artifact-only risk: phishing lookalike domain triggers high risk."""
    req = CheckPaymentRequest(
        input_type="LINK",
        payload="https://secure-upi-paytm-verify-refund.xyz/pay?user=USR-9901&am=25000",
        transaction_context={
            "amount": 25000.0,
            "velocity_1h": 1,
            "device_score": 0.15,
            "location_score": 0.10,
            "merchant_risk": 0.20,
            "account_age_days": 180
        }
    )
    res = payment_forensics_service.analyze_payment(req)
    assert res.risk_score >= 60.0
    assert res.trust_level == "HIGH RISK / UNTRUSTED"
    assert res.decision == "BLOCK"
    # Ensure artifact signal was captured
    artifact_signals = [s for s in res.signal_summary if s.category == "ARTIFACT"]
    assert len(artifact_signals) > 0

def test_transaction_only_risk_fusion():
    """Test transaction-only risk: high amount and velocity burst without image artifact."""
    payload = TransactionPayload(
        txn_id="TXN-BURST-001",
        user_id="USR-BURST",
        amount=89000.0,
        hour=3,
        velocity_1h=12,
        account_age_days=10,
        device_score=0.85,
        location_score=0.75,
        merchant_risk=0.80
    )
    res = fraud_engine.predict(payload)
    assert res.risk_score >= 65.0
    assert res.decision == "BLOCK"
    # Behavioral signal must reflect high severity
    beh_signal = next((s for s in res.signal_summary if s.category == "BEHAVIORAL"), None)
    assert beh_signal is not None
    assert beh_signal.severity in ["HIGH", "CRITICAL"]

def test_multi_signal_corroborated_block():
    """Test multi-signal corroborated fraud: critical forensic + velocity burst + device anomaly -> BLOCK."""
    forensic_signals = [
        {"name": "Credential Harvesting Intent", "severity": "CRITICAL", "status": "OBSERVED", "description": "MPIN entry request"}
    ]
    payload = TransactionPayload(
        txn_id="TXN-CRIT-001",
        user_id="USR-FRAUD",
        amount=45000.0,
        hour=2,
        velocity_1h=8,
        account_age_days=5,
        device_score=0.90,
        location_score=0.80,
        merchant_risk=0.90,
        forensic_signals=forensic_signals
    )
    res = fraud_engine.predict(payload)
    assert res.risk_score >= 70.0
    assert res.decision == "BLOCK"
    assert "IMMEDIATE BLOCK" in (res.recommendation or "")

def test_model_disagreement_and_epistemic_uncertainty():
    """Test model disagreement tracking and confidence decoupling."""
    payload = TransactionPayload(
        txn_id="TXN-AMBIG-001",
        amount=65000.0,
        hour=1,
        velocity_1h=4,
        account_age_days=60,
        device_score=0.60,
        location_score=0.45,
        merchant_risk=0.55
    )
    res = fraud_engine.predict(payload)
    assert res.model_disagreement is not None
    assert isinstance(res.model_disagreement.disagreement_score, float)
    assert res.model_disagreement.epistemic_uncertainty >= 0.0
    # Confidence is decoupled from raw risk score
    assert 0.0 <= res.confidence <= 1.0
    assert "xgboost" in res.model_disagreement.model_spread
    assert "random_forest" in res.model_disagreement.model_spread

def test_cross_signal_inconsistency_detection():
    """Test Cross-Signal Consistency Engine when artifact amount differs from transaction context."""
    payload = TransactionPayload(
        txn_id="TXN-MISMATCH-001",
        amount=850.0, # Transaction context claims 850
        merchant_id="merchant.store@icici",
        artifact_context={
            "amount": 48500.0, # But artifact is requesting 48,500
            "payee_vpa": "fraudster.drain@ybl"
        }
    )
    res = fraud_engine.predict(payload)
    assert res.cross_signal_consistency is not None
    assert res.cross_signal_consistency.status == "INCONSISTENT"
    assert len(res.cross_signal_consistency.conflicts) > 0
    assert any("Amount Mismatch" in c for c in res.cross_signal_consistency.conflicts)

def test_false_positive_mitigation_step_up():
    """Test false-positive protection: aged account + low velocity + new device routes to STEP_UP instead of BLOCK."""
    payload = TransactionPayload(
        txn_id="TXN-MITIGATED-001",
        user_id="USR-LONGTIME",
        account_id="ACC-TRUSTED",
        amount=12000.0,
        hour=15,
        velocity_1h=1,
        account_age_days=450, # Long established account tenure
        device_score=0.72, # Unfamiliar device (e.g. upgraded phone)
        location_score=0.20,
        merchant_risk=0.15 # Trusted merchant
    )
    res = fraud_engine.predict(payload)
    # Even if device score is high, it should not blindly hard block legitimate long-standing customer
    assert res.decision in ["STEP_UP", "MONITOR", "APPROVE"]
    if res.decision == "STEP_UP":
        assert len(res.mitigation_factors) > 0

def test_explicit_unavailable_signal_tracking():
    """Test that missing external feeds are explicitly labeled UNAVAILABLE without synthetic fabrication."""
    payload = TransactionPayload(
        txn_id="TXN-UNAVAIL-001",
        amount=1500.0,
        velocity_1h=1,
        device_score=0.1,
        location_score=0.1,
        merchant_risk=0.1
    )
    res = fraud_engine.predict(payload)
    unavail_signals = [s for s in res.signal_summary if s.status == "UNAVAILABLE"]
    assert len(unavail_signals) > 0
    # Artifact forensics and SIM-swap feed should be labeled UNAVAILABLE
    assert any("Carrier SIM-Swap" in s.name or "Artifact" in s.name for s in unavail_signals)

def test_feature_contributions_shap_decomposition():
    """Test SHAP / feature attribution returns positive and negative contributors."""
    payload = TransactionPayload(
        txn_id="TXN-EXPLAIN-001",
        amount=75000.0,
        velocity_1h=6,
        account_age_days=30,
        device_score=0.70,
        location_score=0.60,
        merchant_risk=0.65
    )
    res = fraud_engine.predict(payload)
    assert len(res.top_positive_contributors) > 0
    assert any(c.direction == "INCREASES_RISK" for c in res.top_positive_contributors)
    # Check FraudDNA axes
    assert res.fraud_dna is not None
    assert "fraud_dna_fingerprint" in res.fraud_dna
    assert len(res.fraud_dna["fraud_dna_fingerprint"]) == 5
