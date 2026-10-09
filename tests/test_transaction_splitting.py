import pytest
import time
from backend.app.services.velocity_engine import velocity_engine

def test_transaction_splitting_sub_threshold():
    # Setup
    user_id = "USR-SPLIT-TEST-1"
    velocity_engine.user_history[user_id] = []
    
    now = time.time()
    velocity_engine.user_history[user_id] = [
        {"time": now - 30, "amount": 9999.0, "device_id": "D1", "ip": "1.1.1.1", "merchant_id": "M1", "lat": 19.0, "lon": 72.8},
        {"time": now - 20, "amount": 9999.0, "device_id": "D1", "ip": "1.1.1.1", "merchant_id": "M1", "lat": 19.0, "lon": 72.8},
        {"time": now - 10, "amount": 9999.0, "device_id": "D1", "ip": "1.1.1.1", "merchant_id": "M1", "lat": 19.0, "lon": 72.8},
    ]
    
    txn = {
        "user_id": user_id,
        "amount": 9999.0,
        "device_id": "D1",
        "ip": "1.1.1.1",
        "merchant_id": "M1"
    }
    
    # Execute
    res = velocity_engine.compute_velocity(txn)
    
    # Assert
    assert res["splitting_result"]["detected"] is True
    assert res["splitting_result"]["pattern_type"] == "SUB_THRESHOLD_STRUCTURING"
    assert res["splitting_result"]["repeated_amounts"] == 4
    assert res["splitting_result"]["sub_threshold_count"] == 4
    assert res["splitting_result"]["confidence"] >= 0.8
    assert res["velocity_risk_score"] > 50.0

def test_no_splitting_on_normal_txns():
    user_id = "USR-SPLIT-TEST-2"
    velocity_engine.user_history[user_id] = []
    
    now = time.time()
    velocity_engine.user_history[user_id] = [
        {"time": now - 30, "amount": 1500.0, "device_id": "D1", "ip": "1.1.1.1", "merchant_id": "M1", "lat": 19.0, "lon": 72.8},
    ]
    
    txn = {
        "user_id": user_id,
        "amount": 2500.0,
        "device_id": "D1"
    }
    
    res = velocity_engine.compute_velocity(txn)
    assert res["splitting_result"]["detected"] is False
    assert res["splitting_result"]["pattern_type"] == "NONE"
