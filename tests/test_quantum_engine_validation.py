import os
import json
import pytest
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.transaction import TransactionPayload
from backend.app.services.fraud_engine import fraud_engine
from backend.app.services.quantum_escalation import quantum_escalation_engine
from backend.app.services.quantum_benchmark import quantum_benchmark_service

client = TestClient(app)

def test_quantum_escalation_genuine_bypassed():
    """Verify that a clear genuine transaction bypasses the quantum circuit to conserve latency."""
    payload = TransactionPayload(
        txn_id="TXN-GENUINE-TEST",
        amount=350.0,
        hour=14,
        velocity_1h=1,
        device_score=0.08,
        location_score=0.05,
        merchant_risk=0.10,
        account_age_days=300
    )
    pred = fraud_engine.predict(payload, enable_quantum=True)
    assert pred.quantum_active is True
    assert pred.quantum_escalation is not None
    assert pred.quantum_escalation.get("circuit_executed") is False
    assert pred.quantum_escalation.get("execution_mode") == "NOT_EXECUTED"
    assert pred.quantum_escalation.get("q_decision_vote") == "BYPASS"

def test_quantum_escalation_borderline_executed():
    """Verify that a borderline transaction escalates and executes the quantum kernel circuit."""
    payload = TransactionPayload(
        txn_id="TXN-BORDERLINE-TEST",
        amount=85000.0,
        hour=23,
        velocity_1h=4,
        device_score=0.55,
        location_score=0.50,
        merchant_risk=0.52,
        account_age_days=60
    )
    pred = fraud_engine.predict(payload, enable_quantum=True)
    assert pred.quantum_active is True
    assert pred.quantum_escalation is not None
    assert pred.quantum_escalation.get("circuit_executed") is True
    assert pred.quantum_escalation.get("execution_mode") == "SIMULATION"
    assert "qsvc_threshold" in pred.quantum_escalation
    assert pred.quantum_escalation.get("qsvc_threshold") == 0.1083
    assert pred.quantum_escalation.get("output_type") == "QSVC_CALIBRATED_PROBABILITY"
    assert "raw_score" in pred.quantum_escalation
    assert pred.quantum_escalation.get("backend_used") == "Qiskit FidelityStatevectorKernel (CPU Statevector Simulation)"

def test_defensive_quantum_fusion_no_risk_reduction():
    """Verify defensive quantum fusion policy: quantum scores below threshold do NOT deduct risk points."""
    # When QSVC outputs score < 0.1083 (GENUINE vote), it should preserve baseline risk with 0 penalty, not -10
    payload = TransactionPayload(
        txn_id="TXN-BORDERLINE-DEFENSIVE",
        amount=85000.0,
        hour=12,
        velocity_1h=3,
        device_score=0.45,
        location_score=0.45,
        merchant_risk=0.45,
        account_age_days=80
    )
    pred = fraud_engine.predict(payload, enable_quantum=True)
    # Check deterministic adjustments in fusion result
    q_adjustments = [
        adj for adj in pred.fusion_result.deterministic_adjustments
        if "QUANTUM_KERNEL" in adj.get("rule", "")
    ]
    assert len(q_adjustments) > 0
    for adj in q_adjustments:
        # None of the adjustments should be negative (no risk suppression)
        assert adj.get("penalty", 0.0) >= 0.0

def test_quantum_escalation_deactivated_when_disabled():
    """Verify clean fallback when enable_quantum is explicitly False."""
    payload = TransactionPayload(
        txn_id="TXN-DISABLE-TEST",
        amount=85000.0,
        hour=23,
        velocity_1h=4,
        device_score=0.55,
        location_score=0.50,
        merchant_risk=0.52
    )
    pred = fraud_engine.predict(payload, enable_quantum=False)
    assert pred.quantum_active is False
    assert pred.quantum_execution_mode == "CLASSICAL_ONLY"
    assert pred.quantum_escalation.get("circuit_executed") is False
    assert pred.quantum_escalation.get("execution_mode") == "NOT_EXECUTED"

def test_quantum_status_api_endpoint():
    """Verify /api/quantum/status exposes accurate hardware readiness and telemetry without physical QPU fabrications."""
    resp = client.get("/api/quantum/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "engine_online" in data
    assert "ibm_hardware_readiness" in data
    assert "ibm_hardware_disclaimer" in data
    assert data["ibm_hardware_token_configured"] is False
    assert data["ibm_quantum_runtime_installed"] is False
    assert data["ibm_hardware_readiness"] == "UNCONFIGURED_LOCAL_SIMULATION_ONLY"
    assert "circuit_telemetry" in data
    assert data["circuit_telemetry"].get("num_qubits") == 4

def test_quantum_benchmark_reproducibility():
    """Verify /api/quantum/benchmark runs reproducibly with proper evaluation metrics."""
    res1 = quantum_benchmark_service.run_ablation_benchmark(n_samples=30)
    res2 = quantum_benchmark_service.run_ablation_benchmark(n_samples=30)

    assert res1["dataset_info"]["dataset_type"] == "SYNTHETIC_EVALUATION"
    assert res1["comparison"]["classical_only"]["precision"] == res2["comparison"]["classical_only"]["precision"]
    assert res1["comparison"]["hybrid_quantum_classical"]["precision"] == res2["comparison"]["hybrid_quantum_classical"]["precision"]
    assert res1["comparison"]["hybrid_quantum_classical"]["simulator"] == "Qiskit FidelityStatevectorKernel (CPU Statevector Simulation)"
    assert res1["comparison"]["hybrid_quantum_classical"]["execution_mode"] == "SIMULATION"
