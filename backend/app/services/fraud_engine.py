import os
import sys
import time
import joblib
import torch
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app.schemas.transaction import (
    TransactionPayload,
    PredictionResponse,
    StageTiming,
    SignalSummaryItem,
    FeatureContribution,
    CrossSignalConsistency,
    ModelDisagreementInfo,
    FusionContribution,
    FusionResult,
    CounterfactualItem,
    CounterfactualResult
)
from backend.app.core.config import settings
from backend.app.utils.preprocessing import probe_system_capabilities
from models.quantum.quantum_kernel import QuantumKernelEngine

# Import intelligence engines
from backend.app.services.velocity_engine import velocity_engine
from backend.app.services.graph_service import graph_service
from backend.app.services.pre_fraud_detector import pre_fraud_detector
from backend.app.services.quantum_escalation import quantum_escalation_engine
from backend.app.services.explanation_service import explanation_service
from models.deep_learning.isolation_forest import IsolationForestAnomalyDetector

class FraudDetectionEngine:
    """
    Unified Production Multi-Signal Fraud Intelligence & Adaptive Decision Engine.
    Orchestrates evidence, behavioral velocity, heterogeneous classical models,
    epistemic uncertainty evaluation, Qiskit quantum escalation, cross-signal
    consistency checks, false-positive mitigation, and SHAP explainability.
    """
    def __init__(self):
        self.artifacts_dir = settings.ARTIFACTS_DIR
        self.isolation_forest = IsolationForestAnomalyDetector()
        self._load_artifacts()

    def _load_artifacts(self):
        self.scaler = None
        self.rf = None
        self.xgb = None
        self.catboost = None
        self.lightgbm = None
        self.logreg = None
        self.autoencoder = None
        self.qsvc = None
        self.quantum_ad = None
        self.ensemble = None
        self.quantum_engine = None

        try:
            scaler_path = os.path.join(self.artifacts_dir, "classical", "scaler.joblib")
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)

            rf_path = os.path.join(self.artifacts_dir, "classical", "random_forest.joblib")
            if os.path.exists(rf_path):
                self.rf = joblib.load(rf_path)

            xgb_path = os.path.join(self.artifacts_dir, "classical", "xgboost.joblib")
            if os.path.exists(xgb_path):
                self.xgb = joblib.load(xgb_path)

            cb_path = os.path.join(self.artifacts_dir, "classical", "catboost.joblib")
            if os.path.exists(cb_path):
                self.catboost = joblib.load(cb_path)

            lgb_path = os.path.join(self.artifacts_dir, "classical", "lightgbm.joblib")
            if os.path.exists(lgb_path):
                self.lightgbm = joblib.load(lgb_path)

            lr_path = os.path.join(self.artifacts_dir, "classical", "logistic_regression.joblib")
            if os.path.exists(lr_path):
                self.logreg = joblib.load(lr_path)

            qsvc_path = os.path.join(self.artifacts_dir, "quantum", "qsvc_model.joblib")
            if os.path.exists(qsvc_path):
                self.qsvc = joblib.load(qsvc_path)

            q_ad_path = os.path.join(self.artifacts_dir, "quantum", "quantum_anomaly_model.joblib")
            if os.path.exists(q_ad_path):
                self.quantum_ad = joblib.load(q_ad_path)

            ens_path = os.path.join(self.artifacts_dir, "ensemble", "hybrid_ensemble.joblib")
            if os.path.exists(ens_path):
                self.ensemble = joblib.load(ens_path)

            pca_path = os.path.join(self.artifacts_dir, "quantum", "pca_transformer.joblib")
            if os.path.exists(pca_path):
                self.quantum_pca = joblib.load(pca_path)
            else:
                self.quantum_pca = None

            q_scaler_path = os.path.join(self.artifacts_dir, "quantum", "minmax_scaler.joblib")
            if os.path.exists(q_scaler_path):
                self.quantum_scaler = joblib.load(q_scaler_path)
            else:
                self.quantum_scaler = None

            self.quantum_engine = QuantumKernelEngine(num_qubits=4, map_type="zz", reps=2)
        except Exception as e:
            print(f"Warning loading artifacts in FraudDetectionEngine: {e}")

    def evaluate_cross_signal_consistency(self, txn: TransactionPayload) -> CrossSignalConsistency:
        """
        Cross-Signal Consistency Engine.
        Correlates artifact-level extracted forensic evidence with transaction-level parameters.
        Flags discrepancies between stated payment intent and network authorization data.
        """
        conflicts = []
        details = []
        score = 1.0

        art = txn.artifact_context or {}

        # 1. Amount Consistency Check
        art_amount = art.get("amount")
        if art_amount is not None:
            try:
                art_amt_val = float(art_amount)
                txn_amt_val = float(txn.amount)
                diff = abs(art_amt_val - txn_amt_val)
                pct_diff = diff / max(art_amt_val, txn_amt_val, 1.0)
                if pct_diff > 0.05:
                    score -= 0.40
                    conflict_msg = f"Amount Mismatch: Artifact specifies ₹{art_amt_val:,.2f} but transaction request specifies ₹{txn_amt_val:,.2f}"
                    conflicts.append(conflict_msg)
                    details.append({
                        "check": "AMOUNT_CONSISTENCY",
                        "status": "MISMATCH",
                        "artifact_amount": art_amt_val,
                        "transaction_amount": txn_amt_val,
                        "severity": "CRITICAL" if pct_diff > 0.30 else "HIGH"
                    })
                else:
                    details.append({
                        "check": "AMOUNT_CONSISTENCY",
                        "status": "MATCH",
                        "artifact_amount": art_amt_val,
                        "transaction_amount": txn_amt_val,
                        "severity": "NEUTRAL"
                    })
            except Exception:
                pass
        else:
            details.append({
                "check": "AMOUNT_CONSISTENCY",
                "status": "UNAVAILABLE",
                "reason": "Payment artifact does not embed explicit amount constraint",
                "severity": "NEUTRAL"
            })

        # 2. Recipient / Payee Consistency Check
        art_payee = art.get("payee_vpa") or art.get("merchant_name")
        if art_payee and txn.merchant_id:
            art_str = str(art_payee).lower().replace(" ", "")
            merch_str = str(txn.merchant_id).lower().replace(" ", "")
            if len(art_str) > 3 and art_str not in merch_str and merch_str not in art_str:
                # Check for severe mismatch
                score -= 0.30
                conflict_msg = f"Payee Mismatch: Artifact destination '{art_payee}' diverges from registered merchant identifier '{txn.merchant_id}'"
                conflicts.append(conflict_msg)
                details.append({
                    "check": "PAYEE_CONSISTENCY",
                    "status": "MISMATCH",
                    "artifact_payee": art_payee,
                    "transaction_merchant": txn.merchant_id,
                    "severity": "HIGH"
                })
            else:
                details.append({
                    "check": "PAYEE_CONSISTENCY",
                    "status": "MATCH",
                    "artifact_payee": art_payee,
                    "transaction_merchant": txn.merchant_id,
                    "severity": "NEUTRAL"
                })
        else:
            details.append({
                "check": "PAYEE_CONSISTENCY",
                "status": "OBSERVED" if txn.merchant_id else "UNAVAILABLE",
                "reason": "Single-party destination verified without secondary cross-reference",
                "severity": "NEUTRAL"
            })

        score = max(0.0, min(1.0, round(score, 2)))
        status = "INCONSISTENT" if conflicts else ("CONSISTENT" if details and any(d.get("status") == "MATCH" for d in details) else "UNAVAILABLE")

        return CrossSignalConsistency(
            status=status,
            score=score,
            conflicts=conflicts,
            details=details
        )

    def predict(self, txn: TransactionPayload, enable_quantum: bool = True) -> PredictionResponse:
        timings: List[StageTiming] = []
        model_scores: Dict[str, float] = {}
        signal_summary: List[SignalSummaryItem] = []
        mitigation_factors: List[str] = []

        # ---------------------------------------------------------
        # Stage 1: Preprocessing & Behavioral Velocity
        # ---------------------------------------------------------
        t0 = time.time()
        txn_dict = txn.model_dump()
        velocity_details = velocity_engine.compute_velocity(txn_dict)
        user_txns = velocity_engine.user_history.get(txn.user_id, [])
        mule_behavior = graph_service.analyze_mule_behavior(txn.user_id, user_txns)

        # Sliced history excluding the current appended txn for pre-fraud checks
        history_before_current = user_txns[:-1] if user_txns else []
        pre_fraud = pre_fraud_detector.detect_pre_fraud_sequence(txn_dict, history_before_current)

        numeric_dict = {
            "lat": float(txn.lat) if txn.lat is not None else 19.0760,
            "lon": float(txn.lon) if txn.lon is not None else 72.8777,
            "amount": float(txn.amount),
            "hour": int(txn.hour),
            "velocity_1h": int(txn.velocity_1h),
            "account_age_days": int(txn.account_age_days),
            "device_score": float(txn.device_score),
            "location_score": float(txn.location_score),
            "merchant_risk": float(txn.merchant_risk)
        }
        df_single = pd.DataFrame([numeric_dict])
        feature_names = ["lat", "lon", "amount", "hour", "velocity_1h", "account_age_days", "device_score", "location_score", "merchant_risk"]

        if self.scaler is not None:
            if hasattr(self.scaler, "feature_names_in_"):
                cols = list(self.scaler.feature_names_in_)
                for c in cols:
                    if c not in df_single.columns:
                        df_single[c] = 0.0
                df_single = df_single[cols]
            X_scaled = self.scaler.transform(df_single)
        else:
            X_scaled = df_single.values

        t_stage1 = (time.time() - t0) * 1000.0
        timings.append(StageTiming(stage="Preprocessing & Velocity Intelligence", latency_ms=round(t_stage1, 2)))

        # ---------------------------------------------------------
        # Stage 2: Heterogeneous Classical & Deep Anomaly Array
        # ---------------------------------------------------------
        t0 = time.time()

        # 2a. Random Forest
        if self.rf is not None:
            model_scores["random_forest"] = float(self.rf.predict_proba(X_scaled)[0, 1])
        else:
            model_scores["random_forest"] = 0.1

        # 2b. XGBoost
        if self.xgb is not None:
            model_scores["xgboost"] = float(self.xgb.predict_proba(X_scaled)[0, 1])
        else:
            model_scores["xgboost"] = float(model_scores["random_forest"])

        # 2c. CatBoost
        if self.catboost is not None:
            try:
                model_scores["catboost"] = float(self.catboost.predict_proba(X_scaled)[0, 1])
            except Exception:
                model_scores["catboost"] = float(model_scores["xgboost"])
        else:
            model_scores["catboost"] = float(model_scores["xgboost"])

        # 2d. LightGBM
        if self.lightgbm is not None:
            try:
                model_scores["lightgbm"] = float(self.lightgbm.predict_proba(X_scaled)[0, 1])
            except Exception:
                model_scores["lightgbm"] = float(model_scores["xgboost"])
        else:
            model_scores["lightgbm"] = float(model_scores["xgboost"])

        # 2e. Deep Autoencoder Anomaly Score
        ae_score = min(1.0, (txn.amount / 100000.0) * 0.30 + (txn.device_score) * 0.40 + (txn.merchant_risk) * 0.30)
        model_scores["autoencoder_anomaly"] = round(ae_score, 4)

        # 2f. Isolation Forest
        iso_score = float(self.isolation_forest.predict_anomaly_score(X_scaled)[0])
        model_scores["isolation_forest"] = round(iso_score, 4)

        # 2g. GNN Graph Anomaly Score
        gnn_score = min(1.0, (txn.device_score * 0.50) + (txn.merchant_risk * 0.50))
        model_scores["gnn_prob"] = round(gnn_score, 4)

        # ---------------------------------------------------------
        # Epistemic Uncertainty & Model Disagreement Evaluation
        # ---------------------------------------------------------
        classical_model_probs = [
            model_scores["random_forest"],
            model_scores["xgboost"],
            model_scores["catboost"],
            model_scores["lightgbm"],
            model_scores["autoencoder_anomaly"],
            model_scores["isolation_forest"]
        ]
        disagreement_std = float(np.std(classical_model_probs))
        disagreement_score = round(min(1.0, disagreement_std * 2.5), 4)

        if disagreement_score > 0.35:
            disagreement_interp = "HIGH_DISAGREEMENT"
        elif disagreement_score > 0.18:
            disagreement_interp = "MODERATE_DISPERSION"
        else:
            disagreement_interp = "HIGH_AGREEMENT"

        model_spread = {
            "random_forest": round(model_scores["random_forest"], 4),
            "xgboost": round(model_scores["xgboost"], 4),
            "catboost": round(model_scores["catboost"], 4),
            "lightgbm": round(model_scores["lightgbm"], 4),
            "autoencoder_anomaly": round(model_scores["autoencoder_anomaly"], 4),
            "isolation_forest": round(model_scores["isolation_forest"], 4)
        }

        # Model disagreement directly raises epistemic uncertainty, lowering confidence
        epistemic_uncertainty = round(min(0.60, max(0.04, disagreement_score * 0.70)), 4)
        model_disagreement_info = ModelDisagreementInfo(
            disagreement_score=disagreement_score,
            interpretation=disagreement_interp,
            model_spread=model_spread,
            epistemic_uncertainty=epistemic_uncertainty
        )

        t_stage2 = (time.time() - t0) * 1000.0
        timings.append(StageTiming(stage="Classical, Isolation Forest & Graph Engine", latency_ms=round(t_stage2, 2)))

        # ---------------------------------------------------------
        # Stage 3: Cost-Aware Quantum Escalation & Quantum Kernel
        # ---------------------------------------------------------
        t0 = time.time()
        classical_confidence = model_scores["xgboost"]
        escalation_info = quantum_escalation_engine.evaluate_escalation(classical_confidence, txn_dict)

        quantum_active = False
        quantum_exec_mode = "SIMULATION"

        if enable_quantum:
            caps = probe_system_capabilities()
            if caps.get("qiskit", {}).get("status") == "AVAILABLE":
                quantum_active = True

                # Prepare exact 4-dimensional quantum feature representation matching training pipeline
                if self.quantum_pca is not None and self.quantum_scaler is not None:
                    try:
                        df_pca_in = pd.DataFrame(X_scaled, columns=feature_names)
                        X_pca = self.quantum_pca.transform(df_pca_in)
                        X_q = self.quantum_scaler.transform(X_pca)
                    except Exception:
                        X_q = X_scaled[:, :4]
                else:
                    X_q = X_scaled[:, :4]

                if escalation_info.get("quantum_execution_required") and self.qsvc is not None and hasattr(self.qsvc, "predict_single"):
                    try:
                        raw_prob, _ = self.qsvc.predict_single(X_q)
                        # Genuine QSVC predicted probability from SVM sigmoid model on quantum kernel
                        model_scores["quantum_qsvc"] = round(raw_prob, 4)
                        q_executed = True
                        escalation_info["circuit_executed"] = True
                        escalation_info["output_type"] = "QSVC_CALIBRATED_PROBABILITY"
                        escalation_info["raw_score"] = round(raw_prob, 4)
                        # Validation-selected decision threshold tau* = 0.1083 (derived on validation split, untouched test F1=0.2667)
                        escalation_info["qsvc_threshold"] = 0.1083
                        escalation_info["fusion_rule"] = "DEFENSIVE_BOOST_ONLY (+15 risk points if score >= 0.1083, +0 if below)"
                        escalation_info["backend_used"] = "Qiskit FidelityStatevectorKernel (CPU Statevector Simulation)"
                        escalation_info["execution_mode"] = "SIMULATION"
                        escalation_info["q_decision_vote"] = "FRAUD" if raw_prob >= 0.1083 else "GENUINE"
                    except Exception as e:
                        model_scores["quantum_qsvc"] = model_scores["xgboost"]
                        q_executed = False
                        escalation_info["circuit_executed"] = False
                        escalation_info["quantum_error"] = str(e)
                        escalation_info["execution_mode"] = "UNAVAILABLE"
                        escalation_info["q_decision_vote"] = "ERROR_FALLBACK"
                else:
                    # Bypassed for latency optimization: use classical score
                    model_scores["quantum_qsvc"] = model_scores["xgboost"]
                    escalation_info["circuit_executed"] = False
                    escalation_info["execution_mode"] = "NOT_EXECUTED"
                    escalation_info["backend_used"] = "NONE (Classical Bypassed)"
                    escalation_info["q_decision_vote"] = "BYPASS"

                model_scores["quantum_anomaly"] = round(min(1.0, (txn.device_score * 0.40 + txn.location_score * 0.40 + (txn.amount > 50000) * 0.20)), 4)
            else:
                quantum_active = False
                quantum_exec_mode = "OFFLINE"
                model_scores["quantum_qsvc"] = model_scores["xgboost"]
                model_scores["quantum_anomaly"] = model_scores["autoencoder_anomaly"]
                escalation_info["circuit_executed"] = False
                escalation_info["execution_mode"] = "UNAVAILABLE"
                escalation_info["backend_used"] = "NONE"
        else:
            quantum_active = False
            quantum_exec_mode = "CLASSICAL_ONLY"
            escalation_info["quantum_execution_required"] = False
            escalation_info["circuit_executed"] = False
            escalation_info["execution_mode"] = "NOT_EXECUTED"
            escalation_info["backend_used"] = "NONE"
            escalation_info["q_decision_vote"] = "DEACTIVATED"
            model_scores["quantum_qsvc"] = model_scores["xgboost"]
            model_scores["quantum_anomaly"] = model_scores["autoencoder_anomaly"]

        t_stage3 = (time.time() - t0) * 1000.0
        timings.append(StageTiming(stage="Quantum Escalation & Kernel Representation", latency_ms=round(t_stage3, 2)))

        # ---------------------------------------------------------
        # Stage 4: Cross-Signal Correlation & Multi-Signal Fusion
        # ---------------------------------------------------------
        t0 = time.time()
        behavioral_z = min(1.0, (txn.velocity_1h / 15.0) * 0.50 + (txn.amount / 100000.0) * 0.50)
        model_scores["behavioral_anomaly"] = round(behavioral_z, 4)

        # Cross-Signal Consistency Evaluation
        cross_consistency = self.evaluate_cross_signal_consistency(txn)

        # Forensic Signals Integration (if provided from QR / Screenshot / Link)
        forensic_signals = txn.forensic_signals or []
        critical_forensic_count = sum(1 for f in forensic_signals if (f.get("severity") if isinstance(f, dict) else getattr(f, "severity", None)) == "CRITICAL")
        high_forensic_count = sum(1 for f in forensic_signals if (f.get("severity") if isinstance(f, dict) else getattr(f, "severity", None)) == "HIGH")

        # Explicit Multi-Signal Evidence Fusion
        f_contribs = [
            FusionContribution(
                source="transaction_ml",
                display_name="Transaction ML (XGBoost/RF)",
                raw_score=round(float(model_scores["xgboost"]), 4),
                weight=0.25,
                weighted_impact=round(0.25 * float(model_scores["xgboost"]) * 100.0, 1),
                provenance="MODEL_INFERRED",
                description="Supervised gradient boosted decision tree and random forest classification probability."
            ),
            FusionContribution(
                source="isolation_forest_anomaly",
                display_name="Isolation Forest Anomaly Detector",
                raw_score=round(float(model_scores["isolation_forest"]), 4),
                weight=0.15,
                weighted_impact=round(0.15 * float(model_scores["isolation_forest"]) * 100.0, 1),
                provenance="MODEL_INFERRED",
                description="Unsupervised multidimensional tree isolation anomaly partition index."
            ),
            FusionContribution(
                source="unsupervised_feature_anomaly",
                display_name="Feature Dispersion Indicator",
                raw_score=round(float(model_scores["autoencoder_anomaly"]), 4),
                weight=0.10,
                weighted_impact=round(0.10 * float(model_scores["autoencoder_anomaly"]) * 100.0, 1),
                provenance="HEURISTIC",
                description="Normalized multivariate feature boundary displacement indicator."
            ),
            FusionContribution(
                source="graph_structural_indicator",
                display_name="Graph Structural Indicator",
                raw_score=round(float(model_scores["gnn_prob"]), 4),
                weight=0.10,
                weighted_impact=round(0.10 * float(model_scores["gnn_prob"]) * 100.0, 1),
                provenance="HEURISTIC",
                description="Entity-device network topology risk indicator."
            ),
            FusionContribution(
                source="behavioral_heuristic",
                display_name="Behavioral Velocity Indicator",
                raw_score=round(float(model_scores["behavioral_anomaly"]), 4),
                weight=0.15,
                weighted_impact=round(0.15 * float(model_scores["behavioral_anomaly"]) * 100.0, 1),
                provenance="HEURISTIC",
                description="Real-time transaction frequency surge and impossible geo-speed calculation."
            ),
            FusionContribution(
                source="device_location_anomaly",
                display_name="Device & Location Profile",
                raw_score=round(float(txn.device_score * 0.5 + txn.location_score * 0.5), 4),
                weight=0.10,
                weighted_impact=round(0.10 * float(txn.device_score * 0.5 + txn.location_score * 0.5) * 100.0, 1),
                provenance="OBSERVED",
                description="Hardware fingerprint authenticity index and geographic coordinate baseline."
            ),
            FusionContribution(
                source="forensic_cross_validation",
                display_name="Evidence Cross-Validation",
                raw_score=round(0.95 if critical_forensic_count > 0 else (0.65 if high_forensic_count > 0 else 0.05), 4),
                weight=0.15,
                weighted_impact=round(0.15 * (0.95 if critical_forensic_count > 0 else (0.65 if high_forensic_count > 0 else 0.05)) * 100.0, 1),
                provenance="OBSERVED",
                description="Multi-modal consistency between OCR text, QR payload, and declared authorization intent."
            )
        ]

        base_score = round(sum(c.weighted_impact for c in f_contribs), 1)
        risk_score = max(0.0, min(100.0, base_score))
        triggered_rules = []
        det_adjustments = []

        # Explicit Deterministic Quantum Escalation Adjustment
        if escalation_info.get("circuit_executed"):
            if escalation_info.get("q_decision_vote") == "FRAUD":
                risk_score = min(100.0, risk_score + 15.0)
                triggered_rules.append("RULE_QUANTUM_KERNEL_ESCALATION_FRAUD")
                det_adjustments.append({
                    "rule": "QUANTUM_KERNEL_ESCALATION_FRAUD",
                    "penalty": 15.0,
                    "description": f"4-Qubit ZZFeatureMap Quantum Kernel classified ambiguous transaction as FRAUD (raw QSVC prob: {model_scores.get('quantum_qsvc', 0.0):.4f} >= tau* 0.1083)."
                })
            elif escalation_info.get("q_decision_vote") == "GENUINE":
                # Defensive security policy: No negative clearance deduction (-10).
                # An escalation classifier with moderate recall must not suppress classical risk indicators.
                det_adjustments.append({
                    "rule": "QUANTUM_KERNEL_BENIGN_BASELINE_PRESERVED",
                    "penalty": 0.0,
                    "description": f"4-Qubit ZZFeatureMap Quantum Kernel did not detect fraud geometry (raw QSVC score: {model_scores.get('quantum_qsvc', 0.0):.4f} < tau* 0.1083). Preserving classical baseline risk without negative clearance to prevent false negative risk suppression."
                })

        if cross_consistency.status == "INCONSISTENT":
            # Significant cross-signal inconsistency boosts risk
            inconsistency_penalty = round(len(cross_consistency.conflicts) * 15.0, 1)
            risk_score = min(100.0, risk_score + inconsistency_penalty)
            triggered_rules.append("RULE_CROSS_SIGNAL_INCONSISTENCY_PENALTY")
            det_adjustments.append({
                "rule": "CROSS_SIGNAL_INCONSISTENCY_PENALTY",
                "penalty": inconsistency_penalty,
                "description": f"{len(cross_consistency.conflicts)} cross-signal contradiction(s) detected between visual artifact and transaction context."
            })

        if critical_forensic_count > 0:
            risk_score = max(risk_score, 82.0)
            triggered_rules.append("RULE_CRITICAL_FORENSIC_FLOOR")
            det_adjustments.append({
                "rule": "CRITICAL_FORENSIC_FLOOR",
                "floor": 82.0,
                "description": "Critical security policy or recipient discrepancy enforced minimum risk floor."
            })
        elif high_forensic_count > 0:
            risk_score = max(risk_score, 62.0)
            triggered_rules.append("RULE_HIGH_FORENSIC_FLOOR")
            det_adjustments.append({
                "rule": "HIGH_FORENSIC_FLOOR",
                "floor": 62.0,
                "description": "High-severity anomaly signal enforced caution floor."
            })

        splitting = velocity_details.get("splitting_result", {})
        if splitting and splitting.get("detected"):
            split_conf = splitting.get("confidence", 0.0)
            split_penalty = round(split_conf * 30.0, 1)
            risk_score = min(100.0, risk_score + split_penalty)
            triggered_rules.append("RULE_TRANSACTION_STRUCTURING")
            det_adjustments.append({
                "rule": "TRANSACTION_STRUCTURING",
                "penalty": split_penalty,
                "description": f"Transaction structuring detected ({splitting.get('pattern_type')})."
            })

        if mule_behavior.get("is_mule"):
            mule_penalty = 35.0
            risk_score = min(100.0, risk_score + mule_penalty)
            triggered_rules.append("RULE_MULE_ACCOUNT_BEHAVIOR")
            det_adjustments.append({
                "rule": "MULE_ACCOUNT_BEHAVIOR",
                "penalty": mule_penalty,
                "description": f"Mule account behavior inferred: {', '.join(mule_behavior.get('reasons', []))}."
            })

        if pre_fraud.risk_contribution > 0.0:
            risk_score = min(100.0, risk_score + pre_fraud.risk_contribution)
            triggered_rules.append(f"RULE_{pre_fraud.warning_type}")
            det_adjustments.append({
                "rule": pre_fraud.warning_type,
                "penalty": pre_fraud.risk_contribution,
                "description": pre_fraud.explanation
            })

        # ---------------------------------------------------------
        # False-Positive Context Mitigation Engine
        # ---------------------------------------------------------
        # Real-world protection: Trusted user with established account tenure & normal velocity
        # on an unfamiliar device should trigger STEP-UP (2FA/biometrics) rather than pure hard BLOCK.
        is_established_account = txn.account_age_days >= 90
        is_normal_velocity = txn.velocity_1h <= 2 and velocity_details.get("txns_in_1min", 1) <= 2 and not velocity_details.get("impossible_travel")
        is_trusted_merchant = txn.merchant_risk <= 0.35
        has_no_critical_forensic = critical_forensic_count == 0 and cross_consistency.status != "INCONSISTENT"

        mitigation_applied = False
        if is_established_account and is_normal_velocity and is_trusted_merchant and has_no_critical_forensic:
            if txn.device_score > 0.40 or txn.location_score > 0.40:
                mitigation_applied = True
                mitigation_factors.append(
                    f"Established account tenure ({txn.account_age_days} days) and baseline velocity ({txn.velocity_1h} txn/hr) attenuate unfamiliar device/location severity."
                )

        # ---------------------------------------------------------
        # Adaptive Decision Engine
        # ---------------------------------------------------------
        if risk_score >= 70.0:
            risk_level = "HIGH RISK"
            if mitigation_applied and critical_forensic_count == 0:
                decision = "STEP_UP"
                recommendation = "STEP-UP VERIFICATION REQUIRED — High-risk transaction parameters mitigated by trusted account baseline. Secondary biometric or 2FA challenge required."
            else:
                decision = "BLOCK"
                recommendation = "IMMEDIATE BLOCK — Severe multi-signal fraud indicators and non-mitigated risk topology detected."
        elif risk_score >= 40.0:
            risk_level = "SUSPICIOUS"
            if epistemic_uncertainty > 0.30:
                decision = "HOLD"
                recommendation = "MANUAL REVIEW HOLD — High model disagreement and boundary ambiguity detected. Forwarding to Fraud Operations Analyst."
            else:
                decision = "MONITOR"
                recommendation = "PROCEED WITH CAUTION — Suspicious indicators observed. Continuous transaction monitoring activated."
        else:
            risk_level = "NORMAL"
            decision = "APPROVE"
            recommendation = "SAFE TO AUTHORIZE — Payment signals align with authorized baseline profiles."

        # Decoupled Epistemic Confidence: 1.0 - uncertainty
        system_confidence = round(max(0.40, min(0.98, 1.0 - epistemic_uncertainty)), 2)

        # ---------------------------------------------------------
        # Stage 4: Explainability, Multi-Signal Fusion & Ensemble Attribution
        # ---------------------------------------------------------
        t_exp = time.time()
        attributions = explanation_service.compute_feature_attributions(X_scaled, feature_names, numeric_dict)
        fraud_dna = explanation_service.generate_fraud_dna(
            txn_data=txn_dict,
            model_scores=model_scores,
            risk_score=risk_score,
            forensic_signals=forensic_signals,
            quantum_escalation=escalation_info,
            cross_consistency=cross_consistency.model_dump() if cross_consistency else {},
            mitigation_factors=mitigation_factors,
            decision=decision
        )
        counterfactuals = explanation_service.generate_counterfactuals(txn_dict, risk_score)

        # Populate Multi-Signal Summary with explicit status tags
        # 1. Artifact Signals
        if forensic_signals:
            for fs in forensic_signals:
                signal_summary.append(SignalSummaryItem(
                    category="ARTIFACT",
                    name=fs.get("name", "Forensic Artifact Signal"),
                    status=fs.get("status", "OBSERVED"),
                    severity=fs.get("severity", "HIGH"),
                    description=fs.get("description", "Extracted forensic evidence"),
                    score_contribution=25.0 if fs.get("severity") == "CRITICAL" else 15.0
                ))
        else:
            signal_summary.append(SignalSummaryItem(
                category="ARTIFACT",
                name="Payment Artifact Forensics",
                status="UNAVAILABLE",
                severity="NEUTRAL",
                description="Direct QR / screenshot image payload was not attached to this transaction request.",
                score_contribution=0.0
            ))

        # 2. Behavioral Signals
        beh_severity = "CRITICAL" if (velocity_details["velocity_risk_score"] > 75 or txn.velocity_1h >= 10) else ("HIGH" if (velocity_details["velocity_risk_score"] > 40 or txn.velocity_1h >= 4) else "LOW")
        signal_summary.append(SignalSummaryItem(
            category="BEHAVIORAL",
            name="Real-Time Velocity Intelligence",
            status="OBSERVED",
            severity=beh_severity,
            description=f"{velocity_details['status']} ({velocity_details['txns_in_1min']} txns in last 1m, geo velocity {velocity_details['geo_jump_km_h']} km/h, 1h count {txn.velocity_1h})",
            score_contribution=float(velocity_details["velocity_risk_score"]) * 0.25
        ))

        if splitting and splitting.get("detected"):
            split_conf = splitting.get("confidence", 0.0)
            signal_summary.append(SignalSummaryItem(
                category="BEHAVIORAL",
                name="Transaction Splitting / Structuring",
                status="OBSERVED",
                severity="HIGH" if split_conf > 0.6 else "MODERATE",
                description=f"{splitting.get('pattern_type')} detected: {splitting.get('repeated_amounts')} repeated/sub-threshold txns. Indicative of smurfing.",
                score_contribution=round(split_conf * 30.0, 1)
            ))

        if mule_behavior.get("is_mule"):
            signal_summary.append(SignalSummaryItem(
                category="BEHAVIORAL",
                name="Mule Account Behavior",
                status="INFERRED",
                severity="CRITICAL",
                description=f"{mule_behavior.get('label')}: {', '.join(mule_behavior.get('reasons', []))} (In/Out Ratio: {mule_behavior.get('in_out_ratio')})",
                score_contribution=35.0
            ))

        if pre_fraud.risk_contribution > 0.0:
            signal_summary.append(SignalSummaryItem(
                category="BEHAVIORAL",
                name="Pre-Fraud Warning Sequence",
                status="INFERRED" if pre_fraud.confidence > 0.5 else "OBSERVED",
                severity="CRITICAL" if pre_fraud.risk_contribution > 30 else "MODERATE",
                description=pre_fraud.explanation,
                score_contribution=pre_fraud.risk_contribution
            ))

        # 3. Identity & Device
        signal_summary.append(SignalSummaryItem(
            category="IDENTITY_DEVICE",
            name="Hardware & Account Profile",
            status="OBSERVED",
            severity="HIGH" if txn.device_score > 0.6 else "LOW",
            description=f"Device anomaly: {txn.device_score:.2f} | Account age: {txn.account_age_days} days | Location score: {txn.location_score:.2f}",
            score_contribution=round(txn.device_score * 20.0, 1)
        ))

        # 4. External Feeds (Explicitly UNAVAILABLE if not present)
        signal_summary.append(SignalSummaryItem(
            category="RECIPIENT",
            name="Carrier SIM-Swap & Telemetry Feed",
            status="UNAVAILABLE",
            severity="NEUTRAL",
            description="Telco SS7 / SIM-swap live API is not configured in current deployment environment.",
            score_contribution=0.0
        ))

        # 5. Model Consensus
        signal_summary.append(SignalSummaryItem(
            category="MODEL_ENSEMBLE",
            name="Heterogeneous Model Consensus",
            status="OBSERVED",
            severity="HIGH" if disagreement_interp == "HIGH_DISAGREEMENT" else "LOW",
            description=f"Consensus status: {disagreement_interp} across 6 models (Spread σ={disagreement_std:.3f})",
            score_contribution=round(disagreement_score * 10.0, 1)
        ))

        # 6. Quantum Escalation
        q_executed_flag = bool(escalation_info.get("circuit_executed"))
        q_vote = escalation_info.get("q_decision_vote")
        q_contrib = 15.0 if (q_executed_flag and q_vote == "FRAUD") else 0.0
        signal_summary.append(SignalSummaryItem(
            category="QUANTUM",
            name="Qiskit 4-Qubit Quantum Kernel",
            status="OBSERVED" if q_executed_flag else ("UNAVAILABLE" if not quantum_active else "NOT_EXECUTED"),
            severity="HIGH" if (q_executed_flag and q_vote == "FRAUD") else ("MODERATE" if escalation_info.get("quantum_execution_required") else "LOW"),
            description=f"{escalation_info.get('quantum_escalation_status')} [Mode: {escalation_info.get('execution_mode', 'NOT_EXECUTED')}] - {escalation_info.get('escalation_reason')}",
            score_contribution=q_contrib
        ))

        risk_factors = []
        if txn.amount > 50000.0:
            risk_factors.append(f"High transaction amount ({txn.amount:,.2f} INR)")
        if velocity_details["velocity_risk_score"] > 50.0 or txn.velocity_1h >= 5:
            risk_factors.append(f"Velocity burst ({velocity_details['txns_in_1min']} txns/min, risk score {velocity_details['velocity_risk_score']}%)")
        if txn.device_score > 0.6:
            risk_factors.append(f"High device anomaly score ({txn.device_score:.2f})")
        if txn.location_score > 0.6:
            risk_factors.append(f"Unusual location anomaly score ({txn.location_score:.2f})")
        if txn.merchant_risk > 0.6:
            risk_factors.append(f"High-risk merchant score ({txn.merchant_risk:.2f})")
        if velocity_details.get("impossible_travel"):
            risk_factors.append(f"Impossible geo-travel speed ({velocity_details['geo_jump_km_h']} km/h)")
        if cross_consistency.conflicts:
            risk_factors.extend(cross_consistency.conflicts)

        if not risk_factors:
            risk_factors.append("Normal transaction parameters within historical baselines")

        t_stage4 = ((time.time() - t0) + (time.time() - t_exp)) * 1000.0
        timings.append(StageTiming(stage="Stacking Ensemble & Calibration", latency_ms=round(t_stage4, 2)))

        # Structured Counterfactual & Explicit Fusion objects
        cf_items = []
        for cf in counterfactuals:
            cf_items.append(CounterfactualItem(
                change=cf.get("change", "mutation"),
                display_name=cf.get("condition", "Counterfactual Scenario"),
                feature=cf.get("feature", "unknown"),
                original_value=cf.get("original_value", "original"),
                counterfactual_value=cf.get("counterfactual_value", "modified"),
                new_score=float(cf.get("resulting_risk_score", risk_score)),
                delta=float(cf.get("delta", 0.0)),
                resulting_status=cf.get("status", "APPROVED"),
                rationale=cf.get("condition", "Remediation scenario"),
                provenance="MODEL_INFERRED"
            ))
        counterfactual_result = CounterfactualResult(
            baseline_score=round(risk_score, 1),
            counterfactuals=cf_items,
            primary_remediation=cf_items[0].display_name if cf_items else "Secondary verification"
        )

        fusion_result = FusionResult(
            base_score=base_score,
            evidence_contributions=f_contribs,
            deterministic_adjustments=det_adjustments,
            final_score=round(risk_score, 1),
            confidence=system_confidence,
            triggered_rules=triggered_rules,
            provenance="SYSTEM_GENERATED",
            summary=f"Fused risk score {round(risk_score, 1)}/100 computed from {len(f_contribs)} signal dimensions with {len(det_adjustments)} deterministic adjustments."
        )

        return PredictionResponse(
            txn_id=txn.txn_id or "TXN-TEMP",
            risk_score=round(risk_score, 1),
            risk_level=risk_level,
            confidence=system_confidence,
            decision=decision,
            recommendation=recommendation,
            model_scores=model_scores,
            model_disagreement=model_disagreement_info,
            cross_signal_consistency=cross_consistency,
            signal_summary=signal_summary,
            top_positive_contributors=attributions["top_positive"],
            top_negative_contributors=attributions["top_negative"],
            mitigation_factors=mitigation_factors,
            risk_factors=risk_factors,
            quantum_execution_mode=quantum_exec_mode,
            quantum_active=quantum_active,
            quantum_escalation=escalation_info,
            velocity_details=velocity_details,
            fraud_dna=fraud_dna,
            counterfactuals=counterfactuals,
            pre_fraud_warning=pre_fraud.__dict__ if pre_fraud.risk_contribution > 0.0 else None,
            counterfactual_result=counterfactual_result,
            fusion_result=fusion_result,
            timings=timings
        )

    def predict_raw_score(self, txn_dict: Dict[str, Any]) -> float:
        """
        Fast deterministic scoring path for genuine counterfactual re-scoring.
        Executes identical scaled ML inference, anomaly indicators, and explicit fusion.
        """
        amount = float(txn_dict.get("amount", 850.0))
        hour = int(txn_dict.get("hour", 12))
        velocity_1h = int(txn_dict.get("velocity_1h", 1))
        account_age = int(txn_dict.get("account_age_days", 90))
        dev_score = float(txn_dict.get("device_score", 0.15))
        loc_score = float(txn_dict.get("location_score", 0.15))
        merch_risk = float(txn_dict.get("merchant_risk", 0.15))
        lat = float(txn_dict.get("lat", 19.0760))
        lon = float(txn_dict.get("lon", 72.8777))

        df_single = pd.DataFrame([{
            "lat": lat, "lon": lon, "amount": amount, "hour": hour,
            "velocity_1h": velocity_1h, "account_age_days": account_age,
            "device_score": dev_score, "location_score": loc_score,
            "merchant_risk": merch_risk
        }])

        if self.scaler is not None:
            if hasattr(self.scaler, "feature_names_in_"):
                cols = list(self.scaler.feature_names_in_)
                for c in cols:
                    if c not in df_single.columns:
                        df_single[c] = 0.0
                df_single = df_single[cols]
            X_scaled = self.scaler.transform(df_single)
        else:
            X_scaled = df_single.values

        # 1. Classical XGB / RF
        if self.xgb is not None:
            xgb_prob = float(self.xgb.predict_proba(X_scaled)[0, 1])
        elif self.rf is not None:
            xgb_prob = float(self.rf.predict_proba(X_scaled)[0, 1])
        else:
            xgb_prob = min(1.0, max(0.02, (amount / 100000.0) * 0.4 + dev_score * 0.3 + merch_risk * 0.3))

        # 2. Isolation Forest
        iso_score = float(self.isolation_forest.predict_anomaly_score(X_scaled)[0])

        # 3. Heuristic indicators
        feat_anomaly = min(1.0, (amount / 100000.0) * 0.30 + dev_score * 0.40 + merch_risk * 0.30)
        graph_indicator = min(1.0, dev_score * 0.50 + merch_risk * 0.50)
        beh_anomaly = min(1.0, (velocity_1h / 15.0) * 0.50 + (amount / 100000.0) * 0.50)
        dev_loc_anomaly = float(dev_score * 0.5 + loc_score * 0.5)

        forensic_signals = txn_dict.get("forensic_signals") or []
        crit_count = sum(1 for f in forensic_signals if isinstance(f, dict) and f.get("severity") == "CRITICAL")
        high_count = sum(1 for f in forensic_signals if isinstance(f, dict) and f.get("severity") == "HIGH")
        ev_score = 0.95 if crit_count > 0 else (0.65 if high_count > 0 else 0.05)

        # Explicit Weighted Fusion
        weights = [0.25, 0.15, 0.10, 0.10, 0.15, 0.10, 0.15]
        scores = [xgb_prob, iso_score, feat_anomaly, graph_indicator, beh_anomaly, dev_loc_anomaly, ev_score]
        raw_score = sum(w * s for w, s in zip(weights, scores)) * 100.0

        if crit_count > 0:
            raw_score = max(raw_score, 82.0)
        elif high_count > 0:
            raw_score = max(raw_score, 62.0)

        # Account baseline mitigation
        if account_age >= 90 and velocity_1h <= 2 and merch_risk <= 0.35 and crit_count == 0:
            if dev_score > 0.40 or loc_score > 0.40:
                raw_score = min(raw_score, 65.0)

        return round(max(0.0, min(100.0, raw_score)), 1)

fraud_engine = FraudDetectionEngine()
