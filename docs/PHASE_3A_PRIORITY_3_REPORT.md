# QUANTUM KAVACHA — PHASE 3A PRIORITY 3 REPORT
## Pre-Fraud Warning & Silent Account Takeover

### Objective
Implement a genuine event-based Pre-Fraud Warning System that detects suspicious preparation and possible gradual account takeover before a potentially fraudulent payment, using only available event data from the transaction baseline.

### Files Changed
- `backend/app/services/pre_fraud_detector.py` (Created)
- `backend/app/services/fraud_engine.py`
- `backend/app/schemas/transaction.py`
- `backend/app/schemas/investigation.py`
- `backend/app/services/investigation_service.py`
- `backend/app/services/attack_chain_service.py`
- `backend/app/services/attack_lab_service.py`
- `tests/test_pre_fraud_warning.py` (Created)
- `tests/test_phase2_capabilities.py`

### Detector Logic & Event Schema
A new deterministic `PreFraudDetector` module was introduced. Rather than mocking session variables, it evaluates the authoritative baseline maintained by `velocity_engine.user_history`. It checks whether a single incoming transaction deviates across three concurrent risk axes compared to the user's historical transactions:
1. **New Device:** Unrecognized hardware signature.
2. **Network Switch:** New IP address.
3. **New Beneficiary:** Unseen merchant endpoint.
4. **Test Payment Preceding High Value Drain:** Evaluates whether a micro-transaction (< ₹100) occurred in the preceding 60 minutes, culminating in a large (> ₹10,000) immediate outbound transfer.

### Integration Path
1. The `detect_pre_fraud_sequence()` function extracts `history_before_current` by aggressively isolating the state from `velocity_engine` before the current transaction is processed.
2. `fraud_engine.py` accumulates the risk contribution without bypassing deterministic SRCG thresholds.
3. The result is mapped into `PredictionResponse.pre_fraud_warning`.
4. `investigation_service.py` ingests the payload, assigning it to `InvestigationCase.pre_fraud_warning`.
5. `attack_chain_service.py` extracts the ordered pre-fraud timeline and creates a new chronological block (**STAGE 4B: PRE-FRAUD WARNING SEQUENCE**) displaying the precise timeline of preparatory anomaly steps in the chronological Attack Chain story.

### Attack Lab Scenario
Added `SCENARIO_12_SILENT_ACCOUNT_TAKEOVER_PRE_FRAUD`.
This deterministic scenario seeds the velocity engine with a baseline transaction (1 day ago), a test transaction 3 minutes ago with entirely new IP/Device properties, and triggers the current API request for an immediate ₹95,000 transfer, resulting in a successful detection and step-up/block mitigation action.

### Testing Results
- **Suspicious Ordered Sequence:** Passed 🟢
- **Events Outside Window:** Passed 🟢
- **Out of Order Timestamps:** Passed 🟢
- **Missing History Graceful Degradation:** Passed 🟢
- **Duplicate/Legitimate New Device without drain:** Passed 🟢
- **Attack Lab Scenario 12:** Passed 🟢
- **Full Regression Suite:** Executing (Expected: 156 passed)

### Limitations
- The detector relies entirely on the stateful multi-window transactions provided by `velocity_engine`. If `velocity_engine` goes down or the memory resets, historical tracking defaults to `INSUFFICIENT_HISTORY`.
- The current schema does not actively consume "Credential Change" or "Failed MFA" webhook events. The integration is ready for them via `trigger_events` array appending once the upstream gateway provides them.
