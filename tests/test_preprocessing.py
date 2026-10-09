import pytest
import pandas as pd
import numpy as np
from backend.app.utils.preprocessing import DatasetAdapter, probe_system_capabilities

def test_capability_probes():
    caps = probe_system_capabilities()
    assert isinstance(caps, dict)
    assert "qiskit" in caps
    assert caps["qiskit"]["status"] in ["AVAILABLE", "UNAVAILABLE"]

def test_dataset_adapter_synthetic():
    # Construct synthetic data frame matching synthetic generator
    df = pd.DataFrame({
        "txn_id": ["TXN-1", "TXN-2", "TXN-3"],
        "user_id": ["USR-1", "USR-2", "USR-3"],
        "account_id": ["ACC-1", "ACC-2", "ACC-3"],
        "device_id": ["DEV-1", "DEV-2", "DEV-3"],
        "ip": ["192.168.1.1", "192.168.1.2", "192.168.1.3"],
        "merchant_id": ["MERCH-1", "MERCH-2", "MERCH-3"],
        "lat": [19.0, 19.1, 19.2],
        "lon": [72.0, 72.1, 72.2],
        "amount": [100.0, 2500.0, 50.0],
        "hour": [10, 23, 14],
        "velocity_1h": [1, 5, 2],
        "account_age_days": [100, 20, 300],
        "device_score": [0.1, 0.8, 0.2],
        "location_score": [0.1, 0.9, 0.1],
        "merchant_risk": [0.2, 0.7, 0.1],
        "label": [0, 1, 0]
    })

    adapter = DatasetAdapter(df)
    caps = adapter.get_capability_flags()
    
    assert caps["has_graph"] is True
    assert caps["has_geo"] is True
    assert caps["has_device"] is True
    assert adapter.target_col == "label"

    X, y = adapter.prepare_features()
    assert "txn_id" not in X.columns
    assert "user_id" not in X.columns
    assert "amount" in X.columns
    assert len(y) == 3

def test_dataset_adapter_creditcard_format():
    # Creditcard format has Class, Time, Amount, V1..V28
    data = {f"V{i}": np.random.randn(20) for i in range(1, 29)}
    data["Time"] = np.arange(20)
    data["Amount"] = np.random.exponential(scale=100, size=20)
    data["Class"] = [0]*18 + [1]*2
    df = pd.DataFrame(data)

    adapter = DatasetAdapter(df)
    caps = adapter.get_capability_flags()
    
    assert caps["has_graph"] is False
    assert caps["has_geo"] is False
    assert caps["has_device"] is False
    assert adapter.target_col == "Class"

    splits = adapter.get_splits(test_size=0.2, val_size=0.2)
    assert splits["is_time_ordered"] is True
    assert len(splits["X_train"]) + len(splits["X_val"]) + len(splits["X_test"]) == 20
