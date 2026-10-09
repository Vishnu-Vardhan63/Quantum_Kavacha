#!/usr/bin/env bash
set -e

echo "=== [1/4] Installing Backend Python Dependencies ==="
pip install -r backend/requirements.txt
pip install lightgbm catboost shap xgboost torch torch-geometric qiskit qiskit-machine-learning qiskit-aer pytest

echo "=== [2/4] Generating Synthetic Payment Data ==="
python scripts/generate_demo_data.py

echo "=== [3/4] Training All Models (Classical, Deep, GNN, Quantum, Ensemble) ==="
python scripts/train_all.py

echo "=== [4/4] Installing Frontend Node Dependencies ==="
cd frontend && npm install && npm run build && cd ..

echo "✅ Setup complete! Run 'make dev-backend' and 'make dev-frontend' to start services."
