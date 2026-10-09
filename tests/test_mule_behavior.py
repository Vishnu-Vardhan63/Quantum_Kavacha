import pytest
import time
from backend.app.services.graph_service import graph_service

def test_mule_insufficient_history():
    # Empty history
    res = graph_service.analyze_mule_behavior("USR-MULE-1", [])
    assert res["is_mule"] is False
    assert res["provenance"] == "INSUFFICIENT_HISTORY"

def test_mule_normal_account():
    # Normal account with more inflows than outflows, long holding time
    now = time.time()
    txns = [
        {"direction": "IN", "amount": 50000, "time": now - 86400 * 2, "merchant_id": "SALARY"},
        {"direction": "OUT", "amount": 500, "time": now - 86400, "merchant_id": "GROCERY"},
        {"direction": "OUT", "amount": 1000, "time": now - 3600, "merchant_id": "BILL"}
    ]
    res = graph_service.analyze_mule_behavior("USR-NORMAL-1", txns)
    assert res["is_mule"] is False
    assert res["in_out_ratio"] < 0.1
    assert "reasons" in res
    assert len(res["reasons"]) == 0

def test_mule_rapid_flow_through():
    # Mule account: High inflow -> immediate outflow to multiple targets
    now = time.time()
    txns = [
        {"direction": "IN", "amount": 100000, "time": now - 300, "merchant_id": "SCAM_VICTIM"},
        {"direction": "OUT", "amount": 33000, "time": now - 200, "merchant_id": "CRYPTO_1"},
        {"direction": "OUT", "amount": 33000, "time": now - 100, "merchant_id": "CRYPTO_2"},
        {"direction": "OUT", "amount": 33000, "time": now - 50, "merchant_id": "ATM_1"}
    ]
    res = graph_service.analyze_mule_behavior("USR-MULE-2", txns)
    assert res["is_mule"] is True
    assert res["in_out_ratio"] == 0.99
    assert res["unique_beneficiaries"] == 3
    assert res["holding_time_mins"] < 5.0
    assert any("High in-flow" in r for r in res["reasons"])
    assert any("Rapid outflow" in r for r in res["reasons"])
    assert any("High beneficiary diversity" in r for r in res["reasons"])

def test_mule_zero_value_edge_case():
    # Edge case: zero inflows, some outflows
    now = time.time()
    txns = [
        {"direction": "IN", "amount": 0, "time": now - 300, "merchant_id": "TEST"},
        {"direction": "OUT", "amount": 100, "time": now - 100, "merchant_id": "TARGET_1"}
    ]
    res = graph_service.analyze_mule_behavior("USR-MULE-3", txns)
    assert res["is_mule"] is False  # Score shouldn't hit 50 just on one outflow
    assert res["in_out_ratio"] == 1.0  # Avoid div by zero
