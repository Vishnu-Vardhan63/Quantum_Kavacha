import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] in ["QUANTUM KAVACHA", "Q-FraudShield"]
    assert "capabilities" in data

def test_predict_endpoint():
    payload = {
        "txn_id": "TXN-TEST-100",
        "user_id": "USR-100",
        "amount": 85000.0,
        "hour": 23,
        "velocity_1h": 12,
        "device_score": 0.78,
        "location_score": 0.82,
        "merchant_risk": 0.76,
        "account_age_days": 40
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["txn_id"] == "TXN-TEST-100"
    assert "risk_score" in data
    assert "timings" in data
    assert len(data["timings"]) == 4

def test_transactions_endpoint():
    response = client.get("/api/transactions?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_quantum_status_endpoint():
    response = client.get("/api/quantum/status")
    assert response.status_code == 200
    data = response.json()
    assert "engine_online" in data
    assert "execution_mode" in data

def test_models_comparison_endpoint():
    response = client.get("/api/models/comparison")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_analytics_endpoint():
    response = client.get("/api/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "risk_distribution" in data

def test_investigation_endpoint():
    response = client.get("/api/investigation/TXN-QF-001")
    assert response.status_code == 200
    data = response.json()
    assert "transaction" in data
    assert "prediction" in data
