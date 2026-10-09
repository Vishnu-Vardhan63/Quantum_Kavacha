import os
import sys

# Ensure project root in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from qiskit.circuit import QuantumCircuit
    from qiskit.circuit.library import zz_feature_map, pauli_feature_map
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False
    QuantumCircuit = None
    zz_feature_map = None
    pauli_feature_map = None

def create_pluggable_feature_map(
    num_qubits: int,
    map_type: str = "zz",
    reps: int = 2,
    entanglement: str = "linear"
) -> QuantumCircuit:
    """
    Creates a Qiskit QuantumCircuit feature map using Qiskit 2.x API ONLY functions.
    Uses the zz_feature_map(...) function (ZZFeatureMap class is deprecated since 2.1).
    Pluggable map_type: 'zz' or 'pauli'.
    """
    if map_type.lower() == "zz":
        # Qiskit 2.x zz_feature_map function
        fm = zz_feature_map(
            feature_dimension=num_qubits,
            reps=reps,
            entanglement=entanglement,
            insert_barriers=True
        )
    elif map_type.lower() == "pauli":
        # Qiskit 2.x pauli_feature_map function
        fm = pauli_feature_map(
            feature_dimension=num_qubits,
            reps=reps,
            paulis=["z", "zz"],
            entanglement=entanglement,
            insert_barriers=True
        )
    else:
        raise ValueError(f"Unsupported feature map type: {map_type}. Must be 'zz' or 'pauli'.")

    return fm
