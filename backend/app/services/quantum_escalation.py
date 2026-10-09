import numpy as np
from typing import Dict, Any

class QuantumEscalationEngine:
    """
    Cost-Aware Quantum Escalation Engine.
    Intelligently routes standard payment volume through fast classical ML,
    invoking the Qiskit 4-qubit Quantum Kernel (ZZ Feature Map + Fidelity Kernel)
    only when classical confidence is low or complex entity relationships exist.
    """
    def __init__(self, uncertainty_low: float = 0.25, uncertainty_high: float = 0.85):
        self.uncertainty_low = uncertainty_low
        self.uncertainty_high = uncertainty_high

    def evaluate_escalation(self, classical_prob: float, txn_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine whether transaction requires Quantum Kernel evaluation."""
        amount = float(txn_data.get("amount", 0.0))
        device_score = float(txn_data.get("device_score", 0.0))
        merchant_risk = float(txn_data.get("merchant_risk", 0.0))
        velocity_1h = int(txn_data.get("velocity_1h", 1))

        # Decision rule for quantum escalation: borderline probability OR complex / high-value topology
        is_uncertain = (self.uncertainty_low <= classical_prob <= self.uncertainty_high) or (
            0.35 <= device_score <= 0.75 and 0.35 <= merchant_risk <= 0.75
        )
        has_complex_structure = (device_score > 0.65 and velocity_1h >= 5) or (amount > 75000.0)

        escalate = is_uncertain or has_complex_structure

        if escalate:
            return {
                "quantum_escalation_status": "ESCALATED_TO_QUANTUM_KERNEL",
                "escalation_reason": "Low Classical Confidence / Complex Anomaly Topology" if is_uncertain else "High-Value Complex Structural Relationship",
                "quantum_execution_required": True,
                "qubits": 4,
                "feature_map": "ZZFeatureMap (reps=2, entanglement='linear')",
                "kernel_type": "FidelityStatevectorKernel",
                "circuit_depth": 22,
                "backend": "Local Qiskit Statevector Simulator (CPU)",
                "execution_mode": "SIMULATION"
            }
        else:
            return {
                "quantum_escalation_status": "PASSED_VIA_FAST_CLASSICAL",
                "escalation_reason": "High Classical Model Confidence — Quantum Bypassed for Latency Optimization",
                "quantum_execution_required": False,
                "qubits": 4,
                "feature_map": "ZZFeatureMap (Standby)",
                "kernel_type": "FidelityStatevectorKernel (Standby)",
                "circuit_depth": 0,
                "backend": "None (Bypassed)",
                "execution_mode": "NOT_EXECUTED"
            }

quantum_escalation_engine = QuantumEscalationEngine()
