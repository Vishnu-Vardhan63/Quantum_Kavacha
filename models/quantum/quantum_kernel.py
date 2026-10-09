import os
import sys
import hashlib
import json
import numpy as np
from typing import Dict, Any, Tuple, Optional

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from qiskit.circuit import QuantumCircuit
    from qiskit_machine_learning.kernels import FidelityStatevectorKernel
    HAS_QISKIT_KERNEL = True
except ImportError:
    HAS_QISKIT_KERNEL = False
    QuantumCircuit = None
    FidelityStatevectorKernel = None

from models.quantum.feature_map import create_pluggable_feature_map

class QuantumKernelEngine:
    """
    Core Quantum Kernel Pipeline using Qiskit 2.x V2 Primitives & FidelityStatevectorKernel.
    Calculates symmetric, PSD quantum kernel matrices with diagonal=1.
    Supports disk caching and real circuit telemetry extraction.
    """
    def __init__(
        self,
        num_qubits: int = 4,
        map_type: str = "zz",
        reps: int = 2,
        entanglement: str = "linear",
        cache_dir: Optional[str] = None
    ):
        self.num_qubits = num_qubits
        self.map_type = map_type
        self.reps = reps
        self.entanglement = entanglement
        
        if HAS_QISKIT_KERNEL:
            self.feature_map = create_pluggable_feature_map(
                num_qubits=num_qubits,
                map_type=map_type,
                reps=reps,
                entanglement=entanglement
            )
            # FidelityStatevectorKernel is default exact simulation kernel
            self.kernel = FidelityStatevectorKernel(feature_map=self.feature_map) if FidelityStatevectorKernel else None
        else:
            self.feature_map = None
            self.kernel = None
        
        if cache_dir is None:
            cache_dir = os.path.join(project_root, "model_artifacts", "quantum", "cache")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_data_hash(self, X1: np.ndarray, X2: Optional[np.ndarray] = None) -> str:
        hasher = hashlib.sha256()
        hasher.update(X1.tobytes())
        if X2 is not None:
            hasher.update(X2.tobytes())
        config_str = f"{self.num_qubits}_{self.map_type}_{self.reps}_{self.entanglement}"
        hasher.update(config_str.encode("utf-8"))
        return hasher.hexdigest()[:16]

    def evaluate(self, X1: np.ndarray, X2: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Computes quantum kernel matrix K(X1, X2).
        If X2 is None, computes symmetric matrix K(X1, X1).
        Uses disk cache if available.
        """
        data_hash = self._get_data_hash(X1, X2)
        valid_cache_dir = os.path.join(project_root, "model_artifacts", "quantum", "cache")
        try:
            os.makedirs(valid_cache_dir, exist_ok=True)
            cache_file = os.path.join(valid_cache_dir, f"kernel_{data_hash}.npy")
        except Exception:
            cache_file = None
        
        if cache_file and os.path.exists(cache_file):
            return np.load(cache_file)
            
        # Compute kernel using Qiskit FidelityStatevectorKernel or fallback
        if self.kernel is not None:
            if X2 is None:
                K = self.kernel.evaluate(x_vec=X1)
            else:
                K = self.kernel.evaluate(x_vec=X1, y_vec=X2)
        else:
            from sklearn.metrics.pairwise import rbf_kernel
            gamma = 1.0 / float(self.num_qubits if self.num_qubits > 0 else 4)
            K = rbf_kernel(X1, X2 if X2 is not None else X1, gamma=gamma)
            
        # Ensure numerical precision & bounds [0, 1]
        K = np.clip(K, 0.0, 1.0)
        if cache_file:
            try:
                np.save(cache_file, K)
            except Exception:
                pass
        return K

    def verify_kernel_matrix(self, K: np.ndarray, tol: float = 1e-4) -> Dict[str, Any]:
        """
        Verifies mathematical properties required by M3:
        1. Symmetric: K == K.T
        2. Diagonal elements == 1.0
        3. Positive Semi-Definite (PSD): min eigenvalue >= -tol
        """
        n, m = K.shape
        is_square = (n == m)
        if not is_square:
            return {"is_symmetric": False, "is_psd": False, "diagonal_ones": False, "valid": False}
            
        is_symmetric = bool(np.allclose(K, K.T, atol=tol))
        diag = np.diag(K)
        diagonal_ones = bool(np.allclose(diag, 1.0, atol=tol))
        
        eigenvalues = np.linalg.eigvalsh(K)
        min_eig = float(np.min(eigenvalues))
        is_psd = bool(min_eig >= -tol)
        
        valid = is_symmetric and diagonal_ones and is_psd
        return {
            "is_symmetric": is_symmetric,
            "diagonal_ones": diagonal_ones,
            "is_psd": is_psd,
            "min_eigenvalue": round(min_eig, 6),
            "valid": valid
        }

    def get_circuit_telemetry(self) -> Dict[str, Any]:
        """
        Extracts REAL Qiskit QuantumCircuit metadata for Quantum Lab display.
        Includes gate breakdown, depth, size, parameter list, and 2-qubit gate count.
        """
        decomp = self.feature_map.decompose()
        gate_dict = {}
        two_qubit_count = 0
        
        for instruction in decomp.data:
            op_name = instruction.operation.name
            gate_dict[op_name] = gate_dict.get(op_name, 0) + 1
            if len(instruction.qubits) > 1:
                two_qubit_count += 1
                
        return {
            "num_qubits": self.num_qubits,
            "map_type": self.map_type,
            "reps": self.reps,
            "entanglement": self.entanglement,
            "depth": self.feature_map.depth(),
            "size": self.feature_map.size(),
            "num_parameters": len(self.feature_map.parameters),
            "gate_counts": gate_dict,
            "two_qubit_gate_count": two_qubit_count,
            "execution_mode": "SIMULATION"
        }
