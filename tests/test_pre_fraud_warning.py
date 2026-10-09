import pytest
import time
from backend.app.services.pre_fraud_detector import pre_fraud_detector
from backend.app.services.fraud_engine import fraud_engine
from backend.app.services.attack_lab_service import attack_lab_service
from backend.app.schemas.transaction import TransactionPayload
from backend.app.services.velocity_engine import velocity_engine

def test_pre_fraud_suspicious_sequence():
    """1. Suspicious ordered event sequence."""
    now = time.time()
    history = [
        {"time": now - 86400, "device_id": "DEV-OLD", "ip": "1.1.1.1", "merchant_id": "MERCH-OLD", "amount": 500, "direction": "OUT"},
        {"time": now - 300, "device_id": "DEV-NEW", "ip": "2.2.2.2", "merchant_id": "MERCH-NEW", "amount": 1.0, "direction": "OUT"}
    ]
    txn = {"user_id": "USR-1", "device_id": "DEV-NEW", "ip": "2.2.2.2", "merchant_id": "MERCH-NEW", "amount": 50000.0}
    res = pre_fraud_detector.detect_pre_fraud_sequence(txn, history)
    assert res.warning_type == "POSSIBLE_ACCOUNT_TAKEOVER"
    assert "TEST_PAYMENT_PRECEDES_HIGH_VALUE" in res.trigger_events
    assert res.risk_contribution == 45.0
    assert len(res.ordered_timeline) >= 2

def test_events_outside_configured_window():
    """2. Events outside the configured window."""
    now = time.time()
    history = [
        {"time": now - 86400, "device_id": "DEV-OLD", "ip": "1.1.1.1", "merchant_id": "MERCH-OLD", "amount": 500, "direction": "OUT"},
        # Test payment was 2 days ago, outside the 1 hour window
        {"time": now - 172800, "device_id": "DEV-NEW", "ip": "2.2.2.2", "merchant_id": "MERCH-NEW", "amount": 1.0, "direction": "OUT"}
    ]
    txn = {"user_id": "USR-1", "device_id": "DEV-NEW", "ip": "2.2.2.2", "merchant_id": "MERCH-NEW", "amount": 50000.0}
    res = pre_fraud_detector.detect_pre_fraud_sequence(txn, history)
    # Shouldn't trigger ATO because test payment was too old
    assert "TEST_PAYMENT_PRECEDES_HIGH_VALUE" not in res.trigger_events
    assert res.warning_type != "POSSIBLE_ACCOUNT_TAKEOVER"

def test_out_of_order_timestamps():
    """3. Out-of-order input timestamps."""
    now = time.time()
    history = [
        {"time": now - 300, "device_id": "DEV-NEW", "ip": "2.2.2.2", "merchant_id": "MERCH-NEW", "amount": 1.0, "direction": "OUT"},
        {"time": now - 86400, "device_id": "DEV-OLD", "ip": "1.1.1.1", "merchant_id": "MERCH-OLD", "amount": 500, "direction": "OUT"}
    ]
    txn = {"user_id": "USR-1", "device_id": "DEV-NEW", "ip": "2.2.2.2", "merchant_id": "MERCH-NEW", "amount": 50000.0}
    res = pre_fraud_detector.detect_pre_fraud_sequence(txn, history)
    # Timeline should be sorted correctly internally
    assert res.warning_type == "POSSIBLE_ACCOUNT_TAKEOVER"
    assert res.ordered_timeline[0]["time"] <= res.ordered_timeline[-1]["time"]

def test_missing_history():
    """4. Missing history."""
    txn = {"user_id": "USR-2", "device_id": "DEV-NEW", "ip": "2.2.2.2", "merchant_id": "MERCH-NEW", "amount": 50000.0}
    res = pre_fraud_detector.detect_pre_fraud_sequence(txn, [])
    assert res.warning_type == "INSUFFICIENT_HISTORY"
    assert res.risk_contribution == 0.0

def test_unavailable_event_source():
    """5. Unavailable event source."""
    now = time.time()
    history = [{"time": now - 86400, "device_id": "DEV-OLD", "ip": "1.1.1.1", "merchant_id": "MERCH-OLD", "amount": 500, "direction": "OUT"}]
    txn = {"user_id": "USR-1", "amount": 50000.0}
    # txn has no device_id, ip, or merchant_id
    res = pre_fraud_detector.detect_pre_fraud_sequence(txn, history)
    assert res.warning_type == "NONE"
    assert res.risk_contribution == 0.0

def test_duplicate_events():
    """6. Duplicate events."""
    now = time.time()
    history = [
        {"time": now - 86400, "device_id": "DEV-OLD", "ip": "1.1.1.1", "merchant_id": "MERCH-OLD", "amount": 500, "direction": "OUT"}
    ]
    txn = {"user_id": "USR-1", "device_id": "DEV-NEW", "ip": "1.1.1.1", "merchant_id": "MERCH-OLD", "amount": 50.0}
    res = pre_fraud_detector.detect_pre_fraud_sequence(txn, history)
    # Only new device, no new IP or merchant
    assert res.trigger_events == ["NEW_DEVICE_OBSERVED"]

def test_legitimate_new_device():
    """7. Legitimate new device."""
    now = time.time()
    history = [
        {"time": now - 86400, "device_id": "DEV-OLD", "ip": "1.1.1.1", "merchant_id": "MERCH-OLD", "amount": 500, "direction": "OUT"}
    ]
    txn = {"user_id": "USR-1", "device_id": "DEV-NEW", "ip": "1.1.1.1", "merchant_id": "MERCH-OLD", "amount": 500.0}
    res = pre_fraud_detector.detect_pre_fraud_sequence(txn, history)
    assert res.warning_type == "NEW_DEVICE_WARNING"
    assert res.risk_contribution == 5.0  # Not a block

def test_risk_fusion_integration():
    """9. Correct risk-fusion integration."""
    payload = TransactionPayload(
        txn_id="TXN-PF-1",
        user_id="USR-PF-1",
        amount=95000.0,
        merchant_id="MERCH-ATT",
        device_id="DEV-ATT",
        ip="2.2.2.2"
    )
    now = time.time()
    velocity_engine.user_history["USR-PF-1"] = [
        {"time": now - 86400, "direction": "OUT", "amount": 500.0, "device_id": "DEV-NORMAL", "ip": "1.1.1.1", "merchant_id": "MERCH-NORM", "lat": 19.0, "lon": 72.8},
        {"time": now - 180, "direction": "OUT", "amount": 1.0, "device_id": "DEV-ATT", "ip": "2.2.2.2", "merchant_id": "MERCH-ATT", "lat": 19.0, "lon": 72.8},
    ]
    res = fraud_engine.predict(payload)
    assert any("Pre-Fraud" in s.name for s in res.signal_summary)
    assert res.pre_fraud_warning is not None
    assert res.pre_fraud_warning["warning_type"] == "POSSIBLE_ACCOUNT_TAKEOVER"

def test_attack_lab_scenario():
    """10. Attack Lab scenario."""
    res = attack_lab_service.execute_scenario("SCENARIO_12_SILENT_ACCOUNT_TAKEOVER_PRE_FRAUD")
    assert res["decision"] in ["STEP_UP", "BLOCK"]
    assert res["risk_score"] > 60.0
    assert any(adj.get("rule") == "POSSIBLE_ACCOUNT_TAKEOVER" for adj in res["fusion_result"].get("deterministic_adjustments", []))

def test_no_hardcoded_decision():
    """11. No hardcoded final decision."""
    # Ensure pre-fraud detector just returns risk_contribution, not a strict 'decision' override
    # that skips the pipeline.
    res = pre_fraud_detector.detect_pre_fraud_sequence({}, [])
    assert not hasattr(res, "decision")
    assert hasattr(res, "risk_contribution")

def test_existing_policy_consistency():
    """12. Existing SRCG/policy consistency."""
    payload = TransactionPayload(
        txn_id="TXN-PF-2",
        user_id="USR-PF-2",
        amount=1.0, # Not high value, shouldn't trigger ATO, just NEW_DEVICE
        merchant_id="MERCH-ATT",
        device_id="DEV-ATT",
        ip="1.1.1.1"
    )
    now = time.time()
    velocity_engine.user_history["USR-PF-2"] = [
        {"time": now - 86400, "direction": "OUT", "amount": 500.0, "device_id": "DEV-NORMAL", "ip": "1.1.1.1", "merchant_id": "MERCH-NORM"}
    ]
    res = fraud_engine.predict(payload)
    # The SRCG/policy should still just APPROVE or MONITOR if risk is low
    assert res.decision in ["APPROVE", "MONITOR"]
