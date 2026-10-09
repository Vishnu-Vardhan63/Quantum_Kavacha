# API Endpoints Documentation

## Endpoints Overview
- `GET /api/health`: System health status and package capability probes.
- `POST /api/predict`: Runs real-time hybrid fraud inference for a single payment.
- `GET /api/transactions`: Retrieves scored payments list.
- `GET /api/fraud-alerts`: Retrieves severity-sorted fraud alerts.
- `GET /api/quantum/status`: Circuit depth, gate breakdown, Qiskit version, and verification status.
- `POST /api/quantum/kernel`: Computes quantum kernel matrix.
- `GET /api/models/comparison`: Returns benchmark comparison dataset.
- `GET /api/analytics`: High-level fraud rates and volume distribution.
- `GET /api/investigation/{txn_id}`: Detailed SOC investigation breakdown.
- `POST /api/simulate/start`: Launches live transaction stream.
- `POST /api/simulate/stop`: Pauses live transaction stream.
- `GET /api/stream`: SSE Server-Sent Events stream.
