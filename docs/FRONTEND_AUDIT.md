# QUANTUM KAVACHA - FRONTEND AUDIT REPORT
**Phase 1A: Repository Audit (Read-Only)**

## A. Architecture
- **Framework & Structure**: The frontend is a React 18 application built with Vite (`vite v6.x`). There is no routing library (e.g., `react-router-dom`). Navigation is entirely handled by a single monolithic state variable (`activeTab`) inside `src/main.jsx`, which spans over 3,000 lines.
- **Dependencies**: Uses `framer-motion` for animations, `recharts` for charts, `lucide-react` for iconography, and `three.js` (`three`, `@types/three`) for 3D graphics.
- **State Management**: React `useState` and `useEffect` at the top level of `App` in `main.jsx`. No Redux, Context API, or Zustand.
- **API Client**: Native `fetch` is used inline inside components and `useEffect` blocks. No Axios or central API client module.
- **Implementation Status**:
  - *Working*: Basic tab switching, component rendering, Vite build process.
  - *Mocked/Hardcoded*: `analytics` (e.g., total transactions hardcoded to 1200 initially, though partially patched in recent edits), 3D Quantum Core implies real-time quantum execution but is a visual decorative loop.
  - *Missing*: True real-time SSE/WebSockets for live telemetry (polls or uses static arrays), authentication/authorization RBAC.

## B. API Inventory
Based on `main.jsx` and backend definitions:
1. **`POST /api/check-payment/forensic`**
   - *Component*: `CheckPaymentWorkspace` / Attack Lab.
   - *Usage*: Submits payload for fraud prediction.
   - *Handling*: Shows loading spinner. Returns `PredictionResponse`.
2. **`GET /api/transactions`**
   - *Component*: `TransactionsWorkspace` (recently added), `FraudAlertsWorkspace` (recently added).
   - *Usage*: Fetches scored transactions. Returns a mix of simulation buffer and `demo_transactions.csv`.
3. **`GET /api/health`**
   - *Component*: `App` top-level polling.
   - *Usage*: Fetches system health, engine status, and `quantum_engine` availability.
4. **`GET /api/drift/metrics`**
   - *Component*: `App` top-level polling.
   - *Usage*: Used for concept drift PSI scores.
5. **`GET /api/explainability/shap?txn_id={id}`**
   - *Component*: `ExplainabilityWorkspace`.
   - *Usage*: Retrieves feature importance.
6. **`POST /api/copilot/chat`**
   - *Component*: `CopilotWorkspace`.
   - *Usage*: Submits analyst queries and case context for AI explanations.

*Deficiencies*: Missing central error handling, lack of `AbortController` for race conditions in fast tab-switching, no normalized caching (e.g., React Query).

## C. Hardcoded and Simulated Behaviour
- **KPIs & Analytics**: The overview dashboard originally relied on hardcoded `1200` total transactions and `7.9%` fraud rate if the API failed to provide them.
- **3D Visualizations**: The `<QuantumCore3D />` and `<TransactionGraph3D />` components render impressive WebGL scenes but do not strictly map 1:1 with real-time graph nodes or quantum circuit execution states.
- **Demo Scenarios**: The Attack Lab and Check Payment forms use hardcoded `checkScenarios` (e.g., `SCENARIO_1_GENUINE_PAYMENT`) to inject perfectly formatted synthetic payloads.
- **Recommendations**: 
  - Add explicit `SYNTHETIC` and `SIMULATION` badges to Attack Lab outputs.
  - Remove decorative 3D scenes if they mislead the user about actual computations (per guidelines: "Do not animate a circuit in a way that implies a computation ran when it did not").
  - Replace hardcoded KPI fallbacks with explicit "UNAVAILABLE" states (partially addressed in Phase 1 engineering).

## D. Performance Claims Verification
Inspecting `model_artifacts/ensemble/metrics.json` and others:
- **Metrics**: Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC are recorded.
- **Values**: The ensemble model reports **1.0 (100%)** across all metrics. 
- **Dataset**: `sample_count: 240` (tn: 221, tp: 19).
- **Latency**: `inference_ms_per_txn` is reported as `0.002` ms for the full ensemble and `0.001` ms for classical ablation.
- **Verdict**: **UNVERIFIED / SYNTHETIC**. The metrics reflect a trivially small, perfectly separable synthetic demo dataset (240 samples), not a calibrated production environment. Claims of 100% accuracy and sub-millisecond latency are artifacts of the demo constraints, not real-world performance.
- **Action**: Do not claim production readiness. Explicitly label the platform as a "Research Prototype" and the dataset as "Synthetic Demo Data".

## E. Decision and Evidence Consistency
- **Labels Found**: `ALLOW`, `BLOCK`, `STEP_UP`, `INVESTIGATE`, `HIGH_RISK`.
- **Inconsistencies**: The UI uses multiple colors for the same risk severity depending on the component. The decision pills are sometimes styled inconsistently.
- **Recommendation**: Create a central `DecisionBadge` and `ProvenanceBadge` component. Standardize severity colors to `--color-safe`, `--color-caution`, `--color-high-risk`, and `--color-critical`.

## F. Runtime and Security Review
- **Port/Server**: Backend runs on FastAPI, frontend on Vite dev server (port 5173).
- **SSE/WebSockets**: No genuine SSE/WebSocket subscriptions found in the frontend. It relies on short-polling or static loads.
- **Security**: No actual authentication (JWT/OAuth) is implemented. Any RBAC or role-switching in the UI is purely cosmetic frontend state.
- **Performance**: Heavy 3D components (`three.js`) cause high GPU usage and layout reflows. The `main.jsx` monolith causes the entire app to re-render on minor state changes.

## G. Verification Baseline
- **Build**: `npm run build` succeeds yielding a `981 kB` JS payload. 
- **Lint/Tests**: No frontend test suite (Jest/Vitest) is currently configured in `package.json`.
- **Diff**: The repository has uncommitted changes related to the previous Phase 1 styling and structural updates.

## H. Prioritized Findings
1. **CRITICAL**: The application lacks real authentication and relies on synthetic data to achieve 100% metrics. (Fix: Document as Research Prototype; add SYNTHETIC labels).
2. **HIGH**: The 3,000-line `main.jsx` monolith is unmaintainable and causes performance bottlenecks. (Fix: Extract workspaces into separate files, implement standard routing or lazy loading).
3. **HIGH**: Missing `AbortController` in `fetch` requests can lead to race conditions during rapid investigation switching.
4. **MEDIUM**: Decorative 3D elements (`QuantumCore3D`) consume resources without adding verifiable analytic value. (Fix: Replace with data-dense tables/metrics).
5. **LOW**: Hardcoded demo fixtures lack clear visual separation from live telemetry. (Fix: Add `ProvenanceBadge`).

**Implementation Sequence Recommendation:**
1. Extract `main.jsx` tabs into isolated components (`src/components/*`) to stabilize the architecture.
2. Standardize API calls into a shared `apiClient.js` with error handling and abort signals.
3. Enforce the Restrained Dark Theme.
4. Implement `ProvenanceBadge` globally to satisfy data honesty rules.
