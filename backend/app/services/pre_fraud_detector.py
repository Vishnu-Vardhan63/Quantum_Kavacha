import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class PreFraudWarningResult:
    warning_id: str
    user_id: str
    warning_type: str
    trigger_events: List[str]
    ordered_timeline: List[Dict[str, Any]]
    detection_window_secs: float
    risk_contribution: float
    confidence: float
    provenance: str
    missing_data_indicators: List[str]
    recommended_action: str
    explanation: str

class PreFraudDetector:
    """
    Detects Silent Account Takeover and Pre-Fraud Sequences.
    Uses canonical transaction history to detect:
    New Device -> IP Change -> New Beneficiary -> Small Test Txn -> High Value Txn.
    """
    def __init__(self):
        pass

    def detect_pre_fraud_sequence(self, txn: Dict[str, Any], history: List[Dict[str, Any]]) -> PreFraudWarningResult:
        user_id = txn.get("user_id", "UNKNOWN")
        now = time.time()
        
        warning_id = f"PFW-{user_id}-{int(now)}"
        
        if not history:
            return PreFraudWarningResult(
                warning_id=warning_id,
                user_id=user_id,
                warning_type="INSUFFICIENT_HISTORY",
                trigger_events=[],
                ordered_timeline=[],
                detection_window_secs=0.0,
                risk_contribution=0.0,
                confidence=0.0,
                provenance="INSUFFICIENT_HISTORY",
                missing_data_indicators=["HISTORICAL_TRANSACTIONS"],
                recommended_action="NONE",
                explanation="No historical data available to establish baseline."
            )
        
        # Analyze history vs current txn
        timeline = []
        trigger_events = []
        missing_data = ["CREDENTIAL_CHANGES", "FAILED_MFA", "SESSION_LOGINS"] # Unavailable in current schema
        
        # Baseline is history older than 1 hour (to isolate the pre-fraud sequence)
        baseline_history = [h for h in history if (now - h.get("time", now)) > 3600]
        if not baseline_history:
            baseline_history = history # fallback

        past_devices = set(h.get("device_id") for h in baseline_history if h.get("device_id"))
        past_ips = set(h.get("ip") for h in baseline_history if h.get("ip"))
        past_merchants = set(h.get("merchant_id") for h in baseline_history if h.get("merchant_id"))
        
        current_device = txn.get("device_id")
        current_ip = txn.get("ip")
        current_merchant = txn.get("merchant_id")
        current_amount = float(txn.get("amount", 0.0))
        
        # 1. New Device
        if current_device and current_device not in past_devices:
            trigger_events.append("NEW_DEVICE_OBSERVED")
            timeline.append({"time": now, "event": "NEW_DEVICE", "details": f"Device {current_device} used for the first time."})
            
        # 2. IP Change
        if current_ip and current_ip not in past_ips:
            trigger_events.append("NETWORK_IP_CHANGE")
            timeline.append({"time": now, "event": "IP_CHANGE", "details": f"IP {current_ip} unseen in baseline."})
            
        # 3. New Beneficiary
        if current_merchant and current_merchant not in past_merchants:
            trigger_events.append("NEW_BENEFICIARY")
            timeline.append({"time": now, "event": "NEW_BENEFICIARY", "details": f"First transfer to {current_merchant}."})
            
        # 4. Small test payment followed by high value
        # Look for small test payment in history (e.g., < 100) within the last hour
        test_payments = [h for h in history if float(h.get("amount", 0.0)) < 100 and h.get("direction") == "OUT" and (now - h.get("time", now)) < 3600]
        
        if test_payments and current_amount > 10000:
            test_txn = test_payments[-1]
            trigger_events.append("TEST_PAYMENT_PRECEDES_HIGH_VALUE")
            timeline.append({
                "time": test_txn.get("time", now), 
                "event": "SMALL_TEST_TRANSACTION", 
                "details": f"Small test transaction of {test_txn.get('amount')} observed."
            })
            timeline.append({
                "time": now, 
                "event": "HIGH_VALUE_TRANSACTION", 
                "details": f"High value transaction of {current_amount} attempted."
            })
            
        timeline.sort(key=lambda x: x.get("time", 0.0))
        
        # Risk Scoring Logic
        risk_contribution = 0.0
        confidence = 0.0
        warning_type = "NONE"
        recommendation = "MONITOR"
        
        # Single new device alone should not mean fraud
        if len(trigger_events) == 1 and "NEW_DEVICE_OBSERVED" in trigger_events:
            risk_contribution = 5.0
            confidence = 0.3
            warning_type = "NEW_DEVICE_WARNING"
            recommendation = "MONITOR"
            explanation = "New device observed, but no other suspicious indicators present."
        elif len(trigger_events) >= 3 and "TEST_PAYMENT_PRECEDES_HIGH_VALUE" in trigger_events:
            risk_contribution = 45.0
            confidence = 0.85
            warning_type = "POSSIBLE_ACCOUNT_TAKEOVER"
            recommendation = "STEP_UP"
            explanation = "Suspicious sequence: " + ", ".join(trigger_events) + ". Indicative of account takeover prior to large drain."
        elif len(trigger_events) >= 2:
            risk_contribution = 20.0
            confidence = 0.6
            warning_type = "PRE_FRAUD_SEQUENCE"
            recommendation = "MONITOR"
            explanation = "Multiple anomalies observed: " + ", ".join(trigger_events) + "."
        else:
            explanation = "Normal activity."
            
        return PreFraudWarningResult(
            warning_id=warning_id,
            user_id=user_id,
            warning_type=warning_type,
            trigger_events=trigger_events,
            ordered_timeline=timeline,
            detection_window_secs=3600.0,
            risk_contribution=risk_contribution,
            confidence=confidence,
            provenance="HEURISTIC" if risk_contribution > 0 else "OBSERVED",
            missing_data_indicators=missing_data,
            recommended_action=recommendation,
            explanation=explanation
        )

pre_fraud_detector = PreFraudDetector()
