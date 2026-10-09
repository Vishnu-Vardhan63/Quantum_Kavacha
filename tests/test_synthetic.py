import pytest
import pandas as pd
from scripts.generate_demo_data import generate_synthetic_transactions

def test_generate_synthetic_transactions():
    df = generate_synthetic_transactions(num_samples=100, seed=42)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 100
    
    expected_cols = [
        "txn_id", "user_id", "account_id", "device_id", "ip", "merchant_id",
        "lat", "lon", "amount", "hour", "velocity_1h", "account_age_days",
        "device_score", "location_score", "merchant_risk", "label"
    ]
    for col in expected_cols:
        assert col in df.columns

    # Verify scripted demo transaction TXN-QF-001 presence & schema requirements
    txn_demo = df[df["txn_id"] == "TXN-QF-001"]
    assert len(txn_demo) == 1
    row = txn_demo.iloc[0]
    assert row["amount"] == 85000.0
    assert row["hour"] == 23
    assert row["velocity_1h"] == 12
    assert row["location_score"] == 0.82
    assert row["device_score"] == 0.78
    assert row["merchant_risk"] == 0.76
    assert row["account_age_days"] == 40
    assert row["label"] == 1
