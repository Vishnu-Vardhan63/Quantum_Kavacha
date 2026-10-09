import os
import json
import numpy as np
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.core.config import settings
from backend.app.utils.preprocessing import probe_system_capabilities
from models.quantum.quantum_kernel import QuantumKernelEngine

router = APIRouter(prefix="/api/quantum", tags=["Quantum Engine"])

class KernelRequest(BaseModel):
    X1: List[List[float]]
    X2: List[List[float]] = None

@router.get("/status", summary="Quantum Engine Status & Circuit Telemetry")
async def get_quantum_status():
    capabilities = probe_system_capabilities()
    
    qiskit_status = capabilities.get("qiskit", {})
    qml_status = capabilities.get("qiskit_machine_learning", {})
    
    circuit_info_path = os.path.join(settings.ARTIFACTS_DIR, "quantum", "circuit_info.json")
    circuit_info = {}
    if os.path.exists(circuit_info_path):
        with open(circuit_info_path, "r") as f:
            circuit_info = json.load(f)
            
    return {
        "engine_online": (qiskit_status.get("status") == "AVAILABLE"),
        "execution_mode": settings.QUANTUM_MODE_DEFAULT,
        "qiskit_version": qiskit_status.get("version"),
        "qiskit_machine_learning_version": qml_status.get("version"),
        "ibm_hardware_token_configured": bool(settings.IBM_QUANTUM_TOKEN),
        "circuit_telemetry": circuit_info
    }

@router.post("/kernel", summary="Compute Fidelity Quantum Kernel Matrix")
async def compute_quantum_kernel(req: KernelRequest):
    try:
        engine = QuantumKernelEngine(num_qubits=len(req.X1[0]) if req.X1 else 4, map_type="zz", reps=2)
        X1 = np.array(req.X1)
        X2 = np.array(req.X2) if req.X2 else None
        
        K = engine.evaluate(X1, X2)
        verification = engine.verify_kernel_matrix(K) if X2 is None else {}
        
        return {
            "kernel_matrix": K.tolist(),
            "shape": list(K.shape),
            "verification": verification,
            "execution_mode": "SIMULATION"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/benchmark", summary="Quantum vs Classical Comparative Benchmark")
async def get_quantum_benchmark():
    """Returns comparative metrics (Precision, Recall, F1, ROC-AUC, Latency) between Classical-Only and Hybrid Quantum."""
    try:
        from backend.app.services.quantum_benchmark import quantum_benchmark_service
        return quantum_benchmark_service.run_ablation_benchmark()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark calculation error: {str(e)}")

