# QUANTUM KAVACHA - BACKEND GAPS & LIMITATIONS
*Identified during Phase 1A Frontend Audit*

## Missing Endpoints & Response Fields
- **Real-time Telemetry (SSE/WebSockets)**: The frontend implies live telemetry updates, but the backend lacks a true Server-Sent Events (SSE) or WebSocket endpoint for live streaming transaction data and alerts. The frontend currently relies on polling or static buffers.
- **Authentication & RBAC**: There are no endpoints for user login, session management, or role-based access control (RBAC). Any role-switching in the UI (e.g., Analyst vs Admin) is entirely mocked on the frontend.
- **System Logs & Audit Trails**: Missing endpoints to fetch historical audit logs or system events.
- **Pagination & Filtering**: Endpoints like `GET /api/transactions` support basic limits but lack robust pagination (e.g., cursor-based or offset/limit) and complex filtering parameters (date ranges, risk score thresholds, decision filters).

## Hardcoded & Heuristic Backend Behaviour
- **Simulation Buffer vs. Real Database**: `GET /api/transactions` and `GET /api/investigation/{transaction_id}` return data from an in-memory `simulation_service.buffer` or fallback to parsing `demo_transactions.csv`. There is no actual persistent transactional database (e.g., PostgreSQL/MongoDB).
- **Synthetic Metrics**: The evaluation metrics generated during training and served to the frontend represent a 1.0 (100%) score across the board on a trivially small dataset (240 samples).
- **Quantum Execution Mocking**: The `quantum_engine` health metrics and capabilities reflect Qiskit Aer simulation states and lack genuine hardware execution fallback telemetry.

## Missing Capabilities
1. **Persistence**: The application loses all transactional state and investigation notes/actions upon backend restart.
2. **True Counterfactual Rescoring**: The explainability endpoint provides SHAP values, but lacks an endpoint to actively "what-if" rescore a transaction by mutating specific features.
3. **Data Lifecycle Controls**: No endpoints or mechanisms to archive, purge, or manage the lifecycle of transactional data.

## Recommended Fixes (Ordered by Severity & Impact)
1. **CRITICAL**: Integrate a genuine persistent data store (e.g., SQLite or PostgreSQL) to replace the in-memory buffer and CSV parsing, enabling robust filtering, pagination, and persistence.
2. **HIGH**: Implement standard JWT/OAuth authentication endpoints and server-enforced RBAC to prevent unauthorized access.
3. **HIGH**: Implement a `/api/stream` Server-Sent Events (SSE) endpoint to push live alerts and transactions to the frontend, eliminating inefficient polling.
4. **MEDIUM**: Introduce realistic evaluation protocols with proper train/test splits on larger, more imbalanced datasets to provide honest, non-1.0 performance metrics to the UI.
5. **MEDIUM**: Expand the `/api/transactions` endpoint to accept comprehensive query parameters (e.g., `date_from`, `date_to`, `min_risk`, `decision`) to support the new `TransactionsWorkspace` and `FraudAlertsWorkspace`.
