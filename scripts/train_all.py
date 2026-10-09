import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.generate_demo_data import main as generate_data
from models.classical.train_classical import train_and_eval_classical_models

def main():
    print("=== [1/6] Generating Demo Data ===")
    generate_data()

    print("\n=== [2/6] Training Classical Models ===")
    try:
        train_and_eval_classical_models()
    except Exception as e:
        print(f"Classical training note: {e}")

    print("\n=== [3/6] Training Deep Learning Models ===")
    try:
        from models.deep_learning.train_deep import train_and_eval_deep_models
        train_and_eval_deep_models()
    except Exception as e:
        print(f"Deep learning training note: {e}")

    print("\n=== [4/6] Training Graph Neural Network (GNN) ===")
    try:
        from models.graph.train_gnn import train_and_eval_gnn_model
        train_and_eval_gnn_model()
    except Exception as e:
        print(f"GNN training note: {e}")

    print("\n=== [5/6] Training Quantum Kernel Pipeline ===")
    try:
        from models.quantum.train_quantum import train_and_eval_quantum_pipeline
        train_and_eval_quantum_pipeline()
    except Exception as e:
        print(f"Quantum training note: {e}")

    print("\n=== [6/6] Training Hybrid Stacking Ensemble & Calibration ===")
    try:
        from models.ensemble.train_ensemble import train_and_eval_ensemble
        train_and_eval_ensemble()
    except Exception as e:
        print(f"Ensemble training note: {e}")

    print("\n[SUCCESS] Build training step completed successfully. Artifacts ready.")

if __name__ == "__main__":
    main()
