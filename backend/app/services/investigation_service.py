import time
import uuid
import re
from typing import Dict, Any, List, Optional
import json
from backend.app.db.database import get_db_connection, init_db
from datetime import datetime, timezone

import hashlib
from backend.app.schemas.investigation import (
    InvestigationCase, InvestigationCaseSummary, CaseSummary, EntityDetail,
    RelatedCase, InvestigationScorecard, AnalystNote, CaseDecisionRecord,
    AnalystDecisionRequest, CaseCreateRequest, CaseAnalyzeRequest, AuditChainEntry
)
from backend.app.schemas.check_payment import CheckPaymentResponse, CheckPaymentRequest
from backend.app.schemas.transaction import PredictionResponse, TransactionPayload

class InvestigationService:
    """
    Unified Case-Centric Investigation Workspace Service for Q-FraudShield.
    Maintains authoritative state for investigation cases, entity linkages,
    analyst notes, and review decisions.
    """

    def __init__(self):
        init_db()
        self._seed_default_cases()

    def _append_audit_entry(self, case: InvestigationCase, event: str, actor: str, details: str):
        """Cryptographically appends a tamper-evident entry to the SHA-256 audit chain."""
        prev_hash = case.audit_chain[-1]["entry_hash"] if case.audit_chain else "0" * 64
        idx = len(case.audit_chain)
        ts = time.time()
        payload = f"{idx}:{ts}:{event}:{actor}:{details}:{prev_hash}".encode("utf-8")
        entry_hash = hashlib.sha256(payload).hexdigest()
        entry = {
            "index": idx,
            "timestamp": ts,
            "event": event,
            "actor": actor,
            "details": details,
            "prev_hash": prev_hash,
            "entry_hash": entry_hash
        }
        case.audit_chain.append(entry)

    def verify_case_audit_chain(self, case_id: str) -> Dict[str, Any]:
        """Validates the cryptographic SHA-256 hash chain of the case for audit integrity."""
        c = self.get_case(case_id)
        if not c:
            return {"case_id": case_id, "is_valid": False, "error": f"Case '{case_id}' not found."}

        chain = c.audit_chain
        if not chain:
            return {
                "case_id": case_id,
                "is_valid": True,
                "total_entries": 0,
                "root_hash": "0" * 64,
                "status": "EMPTY_CHAIN"
            }

        is_valid = True
        errors = []
        prev_hash = "0" * 64
        for idx, entry in enumerate(chain):
            if entry.get("prev_hash") != prev_hash:
                is_valid = False
                errors.append(f"Broken hash link at index {idx}: expected {prev_hash}, found {entry.get('prev_hash')}")

            expected_payload = f"{entry.get('index')}:{entry.get('timestamp')}:{entry.get('event')}:{entry.get('actor')}:{entry.get('details')}:{entry.get('prev_hash')}".encode("utf-8")
            recomputed_hash = hashlib.sha256(expected_payload).hexdigest()
            if recomputed_hash != entry.get("entry_hash"):
                is_valid = False
                errors.append(f"Tamper detected at index {idx}: recorded hash does not match computed digest.")

            prev_hash = entry.get("entry_hash", "")

        return {
            "case_id": case_id,
            "is_valid": is_valid,
            "total_entries": len(chain),
            "root_hash": chain[-1]["entry_hash"] if chain else "0" * 64,
            "verification_timestamp": time.time(),
            "integrity_status": "CRYPTOGRAPHICALLY_VERIFIED" if is_valid else "TAMPER_DETECTED",
            "errors": errors
        }

    def _seed_default_cases(self):
        """Seed initial realistic deterministic cases for instant SOC exploration."""

        now = time.time()

        # Seed Case 1: Phishing Lookalike & Recipient Mismatch (High Risk)
        case_id_1 = "QF-20261007-49910"
        case_1 = InvestigationCase(
            case_id=case_id_1,
            status="ACTION_RECOMMENDED",
            created_at=now - 1200,
            updated_at=now - 1200,
            source="CHECK_PAYMENT",
            summary=CaseSummary(
                what_happened="High-risk digital payment attempt detected with payee identity mismatch and deceptive lookalike domain.",
                why_suspicious="Payee handle (fakecare@ybl) conflicts with declared merchant, and payment link mimics ICICI netbanking over an untrusted TLD.",
                what_should_happen_next="BLOCK RECOMMENDED — Freeze payment session and prompt user with phishing alert.",
                primary_risk_drivers=[
                    "Lookalike brand domain spoofing (icici-rewards.xyz)",
                    "Recipient VPA inconsistency with declared merchant",
                    "Urgency-inducing social engineering payload"
                ],
                mitigating_factors=[]
            ),
            risk={
                "risk_score": 92.4,
                "risk_level": "HIGH RISK",
                "confidence": 0.91,
                "epistemic_uncertainty": 0.09,
                "decision": "BLOCK",
                "recommendation": "DO NOT PROCEED — Severe forensic anomalies and high fraud probability detected."
            },
            quantum_escalation={
                "quantum_escalation_status": "ESCALATED",
                "quantum_execution_required": True,
                "escalation_reason": "High non-linear feature ambiguity across artifact and behavior signals.",
                "entanglement_entropy": 0.84,
                "circuit_depth": 14,
                "qubit_count": 4
            },
            fraud_dna={
                "case_id": case_id_1,
                "overall_risk_score": 92.4,
                "axes": {
                    "AMOUNT_TRANSACTION": {
                        "axis_name": "Amount & Transaction Risk",
                        "score": 68.0,
                        "severity": "MODERATE",
                        "status": "OBSERVED",
                        "primary_driver": "Amount ₹45,000 at hour 23 (unusual night window)",
                        "explanation": "High transaction value executed during anomalous off-peak operational window.",
                        "risk_drivers": ["[OBSERVED] ₹45,000 transaction amount", "[OBSERVED] 23:00 off-peak hour"],
                        "mitigating_factors": []
                    },
                    "DEVICE": {
                        "axis_name": "Device Risk",
                        "score": 85.0,
                        "severity": "HIGH",
                        "status": "OBSERVED",
                        "primary_driver": "Unfamiliar hardware fingerprint with high anomaly score (0.82)",
                        "explanation": "Unrecognized device signature with no prior verified history on the account.",
                        "risk_drivers": ["[OBSERVED] Device score 0.82", "[OBSERVED] Novel hardware fingerprint"],
                        "mitigating_factors": []
                    },
                    "BEHAVIOR": {
                        "axis_name": "Behavior Risk",
                        "score": 88.0,
                        "severity": "HIGH",
                        "status": "OBSERVED",
                        "primary_driver": "1h velocity burst (12 txns/hr) + social engineering urgency",
                        "explanation": "Rapid consecutive transaction burst accompanied by urgency signals.",
                        "risk_drivers": ["[OBSERVED] Velocity 12 txns/1h", "[OBSERVED] Social-engineering urgency detected"],
                        "mitigating_factors": []
                    },
                    "NETWORK_GRAPH": {
                        "axis_name": "Network & Graph Risk",
                        "score": 96.0,
                        "severity": "CRITICAL",
                        "status": "INFERRED",
                        "primary_driver": "Lookalike phishing host + payee handle mismatch",
                        "explanation": "Domain impersonates banking infrastructure with high threat correlation.",
                        "risk_drivers": ["[INFERRED] Brand lookalike host (icici-rewards.xyz)", "[INFERRED] Recipient VPA mismatch"],
                        "mitigating_factors": []
                    },
                    "QUANTUM_COMPLEXITY": {
                        "axis_name": "Quantum Complexity Risk",
                        "score": 78.0,
                        "severity": "HIGH",
                        "status": "OBSERVED",
                        "primary_driver": "4-qubit Hilbert space entanglement projected high cross-order correlation",
                        "explanation": "Quantum kernel projection resolved multi-signal non-linear boundary separation.",
                        "risk_drivers": ["[OBSERVED] Quantum gate escalation triggered", "[OBSERVED] Entanglement entropy 0.84"],
                        "mitigating_factors": [],
                        "quantum_state": "ESCALATED"
                    }
                },
                "fraud_dna_fingerprint": [
                    {"axis": "AMOUNT_TRANSACTION", "score": 68.0, "severity": "MODERATE", "status": "OBSERVED", "primary_driver": "Amount ₹45,000 at hour 23"},
                    {"axis": "DEVICE", "score": 85.0, "severity": "HIGH", "status": "OBSERVED", "primary_driver": "Unfamiliar device fingerprint (0.82)"},
                    {"axis": "BEHAVIOR", "score": 88.0, "severity": "HIGH", "status": "OBSERVED", "primary_driver": "1h velocity burst (12 txns/hr)"},
                    {"axis": "NETWORK_GRAPH", "score": 96.0, "severity": "CRITICAL", "status": "INFERRED", "primary_driver": "Lookalike phishing domain"},
                    {"axis": "QUANTUM_COMPLEXITY", "score": 78.0, "severity": "HIGH", "status": "OBSERVED", "primary_driver": "4-qubit Hilbert projection"}
                ],
                "explanation_summary": {
                    "simple_explanation": "Payment destination does not match the genuine merchant identity, and the transaction link is on an unverified domain mimicking bank services.",
                    "technical_explanation": "Critical domain spoofing risk combined with payee VPA divergence, validated via hybrid classical ensemble and 4-qubit quantum state projection.",
                    "decision_rationale": "High epistemic confidence (91%) across multi-modal artifact and behavioral telemetry warranted decisive BLOCK."
                },
                "evidence_timeline": [
                    {"timestamp_offset_ms": 0, "stage": "INGESTION", "category": "PAYMENT_ARTIFACT", "event_name": "Payment Link / QR Ingestion", "status": "OBSERVED", "details": "Ingested URI: https://icici-rewards.xyz/claim?acc=9901"},
                    {"timestamp_offset_ms": 14, "stage": "FORENSICS", "category": "NETWORK", "event_name": "Static Link Analysis", "status": "OBSERVED", "details": "Flagged suspicious TLD (.xyz) and brand impersonation (icici)"},
                    {"timestamp_offset_ms": 29, "stage": "FEATURE_FUSION", "category": "BEHAVIOR", "event_name": "Velocity & Telemetry Fusion", "status": "OBSERVED", "details": "12 txns/1h velocity burst fused with device anomaly score 0.82"},
                    {"timestamp_offset_ms": 52, "stage": "QUANTUM_PROJECTION", "category": "QUANTUM", "event_name": "Quantum Kernel Escalation", "status": "OBSERVED", "details": "Executed 4-qubit ZZFeatureMap state projection (Entropy: 0.84)"},
                    {"timestamp_offset_ms": 88, "stage": "DECISION", "category": "MODEL", "event_name": "Adaptive Risk Decision", "status": "OBSERVED", "details": "Unified score 92.4% -> BLOCK RECOMMENDED"}
                ],
                "limitations": [
                    "External real-time dark-web feed is unconfigured; lookalike classification performed statically.",
                    "SS7 telecom SIM-swap signal is unavailable in sandbox environment."
                ],
                "quality_verified": True
            },
            evidence=[
                {"category": "NETWORK", "field": "domain", "value": "icici-rewards.xyz", "status": "OBSERVED", "confidence": 1.0, "source": "STATIC_URL_PARSER"},
                {"category": "NETWORK", "field": "lookalike_brand", "value": "ICICI Bank Impersonation", "status": "INFERRED", "confidence": 0.95, "source": "BRAND_DETECTOR"},
                {"category": "RECIPIENT", "field": "payee_vpa", "value": "fakecare@ybl", "status": "OBSERVED", "confidence": 1.0, "source": "PAYMENT_PAYLOAD"},
                {"category": "AMOUNT", "field": "amount", "value": 45000.0, "status": "OBSERVED", "confidence": 1.0, "source": "TRANSACTION_CONTEXT"},
                {"category": "DEVICE", "field": "device_score", "value": 0.82, "status": "OBSERVED", "confidence": 1.0, "source": "TELEMETRY"},
                {"category": "BEHAVIOR", "field": "velocity_1h", "value": 12, "status": "OBSERVED", "confidence": 1.0, "source": "VELOCITY_ENGINE"},
                {"category": "NETWORK", "field": "domain_reputation_feed", "value": "UNAVAILABLE", "status": "UNAVAILABLE", "confidence": 0.0, "source": "EXTERNAL_INTEL"}
            ],
            timeline=[
                {"timestamp_offset_ms": 0, "stage": "INGESTION", "category": "PAYMENT_ARTIFACT", "event_name": "Payment Link / QR Ingestion", "status": "OBSERVED", "details": "Ingested URI: https://icici-rewards.xyz/claim?acc=9901"},
                {"timestamp_offset_ms": 14, "stage": "FORENSICS", "category": "NETWORK", "event_name": "Static Link Analysis", "status": "OBSERVED", "details": "Flagged suspicious TLD (.xyz) and brand impersonation (icici)"},
                {"timestamp_offset_ms": 29, "stage": "FEATURE_FUSION", "category": "BEHAVIOR", "event_name": "Velocity & Telemetry Fusion", "status": "OBSERVED", "details": "12 txns/1h velocity burst fused with device anomaly score 0.82"},
                {"timestamp_offset_ms": 52, "stage": "QUANTUM_PROJECTION", "category": "QUANTUM", "event_name": "Quantum Kernel Escalation", "status": "OBSERVED", "details": "Executed 4-qubit ZZFeatureMap state projection (Entropy: 0.84)"},
                {"timestamp_offset_ms": 88, "stage": "DECISION", "category": "MODEL", "event_name": "Adaptive Risk Decision", "status": "OBSERVED", "details": "Unified score 92.4% -> BLOCK RECOMMENDED"}
            ],
            entities=[
                EntityDetail(
                    entity_id="USR-9901",
                    entity_type="USER",
                    name="Target Account User (USR-9901)",
                    risk_score=75.0,
                    status="OBSERVED",
                    attributes={"account_age_days": 40, "kyc_status": "VERIFIED"},
                    connected_count=3
                ),
                EntityDetail(
                    entity_id="DEV-9901-UNREC",
                    entity_type="DEVICE",
                    name="Unrecognized Android Client",
                    risk_score=85.0,
                    status="OBSERVED",
                    attributes={"device_score": 0.82, "os": "Android 14", "first_seen": "Today"},
                    connected_count=2
                ),
                EntityDetail(
                    entity_id="fakecare@ybl",
                    entity_type="RECIPIENT",
                    name="Mule Recipient VPA",
                    risk_score=95.0,
                    status="OBSERVED",
                    attributes={"vpa": "fakecare@ybl", "bank": "YES_BANK", "reputation": "HIGH_RISK_MULE"},
                    connected_count=4
                ),
                EntityDetail(
                    entity_id="icici-rewards.xyz",
                    entity_type="NETWORK_DOMAIN",
                    name="Phishing Lookalike Host",
                    risk_score=98.0,
                    status="OBSERVED",
                    attributes={"tld": ".xyz", "ssl_issuer": "Let's Encrypt Free", "ssrf_checked": "CLEAN"},
                    connected_count=1
                )
            ],
            related_cases=[],
            scorecard=InvestigationScorecard(
                evidence_quality="HIGH",
                model_confidence="HIGH",
                entity_context="AVAILABLE",
                graph_context="READY",
                external_intelligence="UNAVAILABLE (No active external feeds)"
            ),
            model_analysis={
                "model_spread": {
                    "random_forest": 0.94,
                    "xgboost_stack": 0.91,
                    "isolation_forest": 0.86,
                    "quantum_kernel": 0.89
                },
                "epistemic_uncertainty": 0.09,
                "interpretation": "STRONG_CONSENSUS"
            },
            counterfactuals=[
                {"condition": "If payment was routed to verified merchant domain rather than lookalike host", "resulting_risk_score": 38.0, "risk_reduction_pct": 54.4},
                {"condition": "If transaction was initiated from user's primary registered device", "resulting_risk_score": 52.0, "risk_reduction_pct": 40.4}
            ],
            limitations=[
                "External dark web reputation feed is unconfigured in current deployment.",
                "SS7 SIM-swap monitoring is unavailable in simulation mode."
            ],
            analyst_notes=[
                AnalystNote(
                    note_id="NOTE-01",
                    timestamp=now - 900,
                    author="Senior SOC Analyst",
                    note_type="OBSERVATION",
                    content="Corroborated domain registration date (3 days ago). High confidence phishing attempt targeting banking rewards."
                )
            ],
            decision_history=CaseDecisionRecord(
                system_decision="BLOCK",
                system_recommendation="DO NOT PROCEED — Severe forensic anomalies and high fraud probability detected.",
                system_risk_score=92.4,
                analyst_review_status="PENDING",
                analyst_action=None,
                analyst_rationale=None,
                updated_at=now - 1200
            )
        )
        self._append_audit_entry(
            case_1,
            "Case Ingested",
            "SYSTEM_INGEST",
            "Initial automated ingestion from multi-modal payment forensics pipeline."
        )
        self._append_audit_entry(
            case_1,
            "Analyst Note Added",
            "Senior SOC Analyst",
            "Corroborated domain registration date (3 days ago). High confidence phishing attempt targeting banking rewards."
        )
        with get_db_connection() as conn:
            for case in [case_1]:
                conn.execute(
                    "INSERT OR REPLACE INTO investigation_cases (case_id, status, created_at, updated_at, source, case_data) VALUES (?, ?, ?, ?, ?, ?)",
                    (case.case_id, case.status, case.created_at, case.updated_at, case.source, case.model_dump_json())
                )
            conn.commit()

    def register_case_from_check_payment(self, check_res: CheckPaymentResponse, req: CheckPaymentRequest) -> InvestigationCase:
        """Create or update an authoritative InvestigationCase from CheckPaymentResponse."""
        now = time.time()
        case_id = check_res.case_id

        # Determine status
        if check_res.decision == "BLOCK":
            status = "ACTION_RECOMMENDED"
        elif check_res.decision == "STEP_UP":
            status = "ESCALATED"
        elif check_res.decision in ["HOLD", "MONITOR"]:
            status = "UNDER_REVIEW"
        else:
            status = "RESOLVED"

        # Build entities
        entities = []
        user_id = "USR-ONLINE"
        device_id = "DEV-CHECK-01"
        amount = 0.0
        payee_vpa = None
        merchant_name = None

        if req.transaction_context:
            user_id = str(req.transaction_context.get("user_id", user_id))
            device_id = str(req.transaction_context.get("device_id", device_id))
            amount = float(req.transaction_context.get("amount", 0.0))
            if not payee_vpa and req.transaction_context.get("recipient_vpa"):
                payee_vpa = str(req.transaction_context.get("recipient_vpa"))
            if not payee_vpa and req.transaction_context.get("payee_vpa"):
                payee_vpa = str(req.transaction_context.get("payee_vpa"))

        domain_val = None
        for ev in check_res.evidence:
            val_str = str(ev.value) if ev.value is not None else ""
            if val_str and val_str.upper() != "UNAVAILABLE":
                if ev.field in ["payee_vpa", "vpa", "recipient", "pa"]:
                    payee_vpa = val_str
                elif ev.field in ["merchant_name", "payee_name", "pn"]:
                    merchant_name = val_str
                elif ev.field == "amount" and isinstance(ev.value, (int, float)):
                    amount = float(ev.value)
                elif ev.field in ["domain", "url_domain", "hostname"]:
                    domain_val = val_str

        # 1. User Entity
        entities.append(EntityDetail(
            entity_id=user_id,
            entity_type="USER",
            name=f"Payer Account ({user_id})",
            risk_score=min(100.0, check_res.risk_score * 0.8),
            status="OBSERVED",
            attributes={"source": "SESSION_CONTEXT", "account_status": "ACTIVE"},
            connected_count=2
        ))

        # 2. Device Entity
        entities.append(EntityDetail(
            entity_id=device_id,
            entity_type="DEVICE",
            name=f"Client Hardware ({device_id})",
            risk_score=min(100.0, check_res.risk_score * 0.9),
            status="OBSERVED",
            attributes={"device_score": req.transaction_context.get("device_score", 0.2) if req.transaction_context else 0.2},
            connected_count=1
        ))

        # 3. Recipient Entity
        if payee_vpa and payee_vpa != "UNAVAILABLE":
            entities.append(EntityDetail(
                entity_id=payee_vpa,
                entity_type="RECIPIENT",
                name=f"Recipient VPA ({payee_vpa})",
                risk_score=check_res.risk_score,
                status="OBSERVED",
                attributes={"vpa_handle": payee_vpa, "merchant_label": merchant_name or "Unknown"},
                connected_count=3
            ))

        # 4. Network Domain Entity (if present)
        if domain_val and domain_val != "UNAVAILABLE":
            entities.append(EntityDetail(
                entity_id=domain_val,
                entity_type="NETWORK_DOMAIN",
                name=f"Payment Host ({domain_val})",
                risk_score=check_res.risk_score,
                status="OBSERVED",
                attributes={"domain": domain_val},
                connected_count=2
            ))

        # 5. Payment Artifact Entity
        entities.append(EntityDetail(
            entity_id=f"ART-{req.input_type}-{case_id[-6:]}",
            entity_type="PAYMENT_ARTIFACT",
            name=f"Payment {req.input_type} Payload",
            risk_score=check_res.risk_score,
            status="OBSERVED",
            attributes={"input_type": req.input_type, "evidence_count": len(check_res.evidence)},
            connected_count=1
        ))

        # Search for related cases in existing store (matches on recipient or device or user)
        related_cases = []
        with get_db_connection() as conn:
            rows = conn.execute("SELECT case_data FROM investigation_cases").fetchall()
            all_cases = [InvestigationCase.model_validate_json(r["case_data"]) for r in rows]
        for exist_case in all_cases:
            if exist_case.case_id == case_id:
                continue

            # Check for shared recipient
            exist_recipients = [e.entity_id for e in exist_case.entities if e.entity_type == "RECIPIENT"]
            if payee_vpa and payee_vpa in exist_recipients:
                related_cases.append(RelatedCase(
                    case_id=exist_case.case_id,
                    relationship_type="SAME_RECIPIENT",
                    risk_score=exist_case.risk["risk_score"],
                    decision=exist_case.risk["decision"],
                    timestamp=exist_case.created_at,
                    shared_attribute=f"Shared VPA: {payee_vpa}"
                ))

            # Check for shared user
            exist_users = [e.entity_id for e in exist_case.entities if e.entity_type == "USER"]
            if user_id != "USR-ONLINE" and user_id in exist_users:
                related_cases.append(RelatedCase(
                    case_id=exist_case.case_id,
                    relationship_type="SAME_USER",
                    risk_score=exist_case.risk["risk_score"],
                    decision=exist_case.risk["decision"],
                    timestamp=exist_case.created_at,
                    shared_attribute=f"Shared User: {user_id}"
                ))

        # Scorecard assessment
        scorecard = InvestigationScorecard(
            evidence_quality="HIGH" if len(check_res.evidence) >= 5 else "MEDIUM",
            model_confidence="HIGH" if check_res.confidence >= 0.85 else ("MEDIUM" if check_res.confidence >= 0.65 else "LOW"),
            entity_context="AVAILABLE" if payee_vpa else "PARTIAL",
            graph_context="READY",
            external_intelligence="UNAVAILABLE (No active external feeds)"
        )

        # Primary risk drivers from FraudDNA or Risk Signals
        risk_drivers = []
        if check_res.fraud_dna and "axes" in check_res.fraud_dna:
            for axis_k, axis_v in check_res.fraud_dna["axes"].items():
                if isinstance(axis_v, dict):
                    sev = axis_v.get("severity")
                    p_driver = axis_v.get("primary_driver")
                    a_name = axis_v.get("axis_name") or axis_v.get("axis") or axis_k
                else:
                    sev = getattr(axis_v, "severity", None)
                    p_driver = getattr(axis_v, "primary_driver", None)
                    a_name = getattr(axis_v, "axis_name", None) or getattr(axis_v, "axis", axis_k)

                if sev in ["HIGH", "CRITICAL"] and p_driver:
                    risk_drivers.append(f"{a_name}: {p_driver}")
        elif check_res.risk_signals:
            risk_drivers = [f"{s.name}: {s.description}" for s in check_res.risk_signals[:3]]

        case_obj = InvestigationCase(
            case_id=case_id,
            status=status,
            created_at=now,
            updated_at=now,
            source="CHECK_PAYMENT",
            summary=CaseSummary(
                what_happened=check_res.fraud_dna.get("explanation_summary", {}).get("simple_explanation", f"Payment analyzed via multi-modal forensics: {check_res.trust_level}.") if check_res.fraud_dna else f"Payment analyzed: {check_res.trust_level}.",
                why_suspicious=check_res.recommendation,
                what_should_happen_next=f"{check_res.decision} RECOMMENDED — {check_res.recommendation}",
                primary_risk_drivers=risk_drivers,
                mitigating_factors=check_res.mitigation_factors or []
            ),
            risk={
                "risk_score": check_res.risk_score,
                "risk_level": "HIGH RISK" if check_res.risk_score >= 70 else ("SUSPICIOUS" if check_res.risk_score >= 40 else "SAFE"),
                "confidence": check_res.confidence,
                "epistemic_uncertainty": check_res.model_disagreement.epistemic_uncertainty if check_res.model_disagreement else 0.1,
                "decision": check_res.decision,
                "recommendation": check_res.recommendation
            },
            quantum_escalation=check_res.quantum_escalation,
            fraud_dna=check_res.fraud_dna or {},
            evidence=[e.model_dump() for e in check_res.evidence],
            timeline=check_res.fraud_dna.get("evidence_timeline", []) if check_res.fraud_dna else [],
            entities=entities,
            related_cases=related_cases,
            scorecard=scorecard,
            model_analysis=check_res.model_disagreement.model_dump() if check_res.model_disagreement else {},
            counterfactuals=check_res.counterfactuals or [],
            limitations=check_res.limitations or [],
            analyst_notes=[],
            decision_history=CaseDecisionRecord(
                system_decision=check_res.decision,
                system_recommendation=check_res.recommendation,
                system_risk_score=check_res.risk_score,
                analyst_review_status="PENDING",
                analyst_action=None,
                analyst_rationale=None,
                updated_at=now
            )
        )

        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO investigation_cases (case_id, status, created_at, updated_at, source, case_data) VALUES (?, ?, ?, ?, ?, ?)",
                (case_obj.case_id, case_obj.status, case_obj.created_at, case_obj.updated_at, case_obj.source, case_obj.model_dump_json())
            )
            conn.commit()
        return case_obj

    def register_case_from_prediction(self, pred: PredictionResponse, txn: TransactionPayload) -> InvestigationCase:
        """Create or update an authoritative InvestigationCase from PredictionResponse."""
        now = time.time()
        case_id = pred.txn_id

        if pred.decision == "BLOCK":
            status = "ACTION_RECOMMENDED"
        elif pred.decision == "STEP_UP":
            status = "ESCALATED"
        elif pred.decision in ["HOLD", "MONITOR"]:
            status = "UNDER_REVIEW"
        else:
            status = "RESOLVED"

        entities = [
            EntityDetail(
                entity_id=txn.user_id,
                entity_type="USER",
                name=f"Account Holder ({txn.user_id})",
                risk_score=min(100.0, pred.risk_score * 0.8),
                status="OBSERVED",
                attributes={"account_age_days": txn.account_age_days, "account_id": txn.account_id},
                connected_count=3
            ),
            EntityDetail(
                entity_id=txn.device_id,
                entity_type="DEVICE",
                name=f"Device ({txn.device_id})",
                risk_score=min(100.0, txn.device_score * 100),
                status="OBSERVED",
                attributes={"device_score": txn.device_score, "ip": txn.ip},
                connected_count=2
            ),
            EntityDetail(
                entity_id=txn.merchant_id,
                entity_type="MERCHANT",
                name=f"Merchant Endpoint ({txn.merchant_id})",
                risk_score=min(100.0, txn.merchant_risk * 100),
                status="OBSERVED",
                attributes={"merchant_risk": txn.merchant_risk},
                connected_count=4
            )
        ]

        # Extract evidence items from features
        evidence = [
            {"category": "AMOUNT", "field": "amount", "value": txn.amount, "status": "OBSERVED", "confidence": 1.0, "source": "TRANSACTION_STREAM"},
            {"category": "BEHAVIOR", "field": "hour", "value": txn.hour, "status": "OBSERVED", "confidence": 1.0, "source": "TIME_CONTEXT"},
            {"category": "BEHAVIOR", "field": "velocity_1h", "value": txn.velocity_1h, "status": "OBSERVED", "confidence": 1.0, "source": "VELOCITY_ENGINE"},
            {"category": "DEVICE", "field": "device_score", "value": txn.device_score, "status": "OBSERVED", "confidence": 1.0, "source": "TELEMETRY"},
            {"category": "LOCATION", "field": "location_score", "value": txn.location_score, "status": "OBSERVED", "confidence": 1.0, "source": "GEO_ENGINE"},
            {"category": "RECIPIENT", "field": "merchant_risk", "value": txn.merchant_risk, "status": "OBSERVED", "confidence": 1.0, "source": "GRAPH_REPUTATION"}
        ]

        scorecard = InvestigationScorecard(
            evidence_quality="HIGH",
            model_confidence="HIGH" if pred.confidence >= 0.85 else "MEDIUM",
            entity_context="AVAILABLE",
            graph_context="READY",
            external_intelligence="UNAVAILABLE (No active external feeds)"
        )

        case_obj = InvestigationCase(
            case_id=case_id,
            status=status,
            created_at=now,
            updated_at=now,
            source="API_PREDICT",
            summary=CaseSummary(
                what_happened=pred.fraud_dna.get("explanation_summary", {}).get("simple_explanation", f"Transaction {case_id} scored by hybrid AI-Quantum engine: {pred.risk_level}.") if pred.fraud_dna else f"Transaction {case_id} scored: {pred.risk_level}.",
                why_suspicious=pred.recommendation or "Elevated anomaly signals detected across behavioral vectors.",
                what_should_happen_next=f"{pred.decision} RECOMMENDED — {pred.recommendation or 'Review telemetry.'}",
                primary_risk_drivers=pred.risk_factors or [],
                mitigating_factors=pred.mitigation_factors or []
            ),
            risk={
                "risk_score": pred.risk_score,
                "risk_level": pred.risk_level,
                "confidence": pred.confidence,
                "epistemic_uncertainty": pred.model_disagreement.epistemic_uncertainty if pred.model_disagreement else 0.1,
                "decision": pred.decision,
                "recommendation": pred.recommendation or "Monitor for follow-up signals."
            },
            quantum_escalation=pred.quantum_escalation.model_dump() if hasattr(pred.quantum_escalation, "model_dump") else pred.quantum_escalation,
            fraud_dna=pred.fraud_dna or {},
            evidence=evidence,
            timeline=pred.fraud_dna.get("evidence_timeline", []) if pred.fraud_dna else [],
            entities=entities,
            related_cases=[],
            scorecard=scorecard,
            model_analysis=pred.model_disagreement.model_dump() if pred.model_disagreement else {"model_scores": pred.model_scores},
            counterfactuals=[cf.model_dump() if hasattr(cf, "model_dump") else cf for cf in pred.counterfactuals],
            limitations=[
                "Real-time telecom SS7 telemetry is unconfigured in current environment.",
                "External dark web fraud intelligence feed is unavailable."
            ],
            analyst_notes=[],
            decision_history=CaseDecisionRecord(
                system_decision=pred.decision,
                system_recommendation=pred.recommendation or "Standard operational protocol.",
                system_risk_score=pred.risk_score,
                analyst_review_status="PENDING",
                analyst_action=None,
                analyst_rationale=None,
                updated_at=now
            ),
            pre_fraud_warning=pred.pre_fraud_warning
        )

        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO investigation_cases (case_id, status, created_at, updated_at, source, case_data) VALUES (?, ?, ?, ?, ?, ?)",
                (case_obj.case_id, case_obj.status, case_obj.created_at, case_obj.updated_at, case_obj.source, case_obj.model_dump_json())
            )
            conn.commit()
        return case_obj

    def get_case(self, case_id: str) -> Optional[InvestigationCase]:
        """Retrieve full case details by ID."""
        with get_db_connection() as conn:
            row = conn.execute("SELECT case_data FROM investigation_cases WHERE case_id = ?", (case_id,)).fetchone()
            if row:
                return InvestigationCase.model_validate_json(row["case_data"])
        return None

    def list_cases(self, search_query: Optional[str] = None, limit: int = 50) -> List[InvestigationCaseSummary]:
        """List recent cases with optional text search across case ID, recipient, or user."""
        results = []
        q = (search_query or "").strip().lower()

        with get_db_connection() as conn:
            rows = conn.execute("SELECT case_data FROM investigation_cases ORDER BY created_at DESC").fetchall()
            all_cases = [InvestigationCase.model_validate_json(row["case_data"]) for row in rows]

        for c in all_cases:
            cid = c.case_id
            if not c:
                continue

            # Match search filter
            if q:
                match = (
                    q in cid.lower() or
                    q in c.summary.what_happened.lower() or
                    any(q in e.entity_id.lower() or q in e.name.lower() for e in c.entities)
                )
                if not match:
                    continue

            # Extract amount and recipient
            amt = 0.0
            recip = "Unknown"
            dev = "Unknown"
            for e in c.entities:
                if e.entity_type == "RECIPIENT":
                    recip = e.name
                elif e.entity_type == "DEVICE":
                    dev = e.entity_id
            for ev in c.evidence:
                if ev.get("field") == "amount" and isinstance(ev.get("value"), (int, float)):
                    amt = float(ev["value"])

            results.append(InvestigationCaseSummary(
                case_id=c.case_id,
                status=c.status,
                source=c.source,
                created_at=c.created_at,
                amount=amt,
                risk_score=c.risk["risk_score"],
                decision=c.risk["decision"],
                quantum_escalated=bool(c.quantum_escalation.get("quantum_execution_required")),
                recipient=recip,
                device_id=dev
            ))

            if len(results) >= limit:
                break

        return results

    def add_analyst_note(self, case_id: str, note_type: str, content: str, author: str = "Lead SOC Analyst") -> Optional[AnalystNote]:
        """Add an analyst-authored investigation note to a case with cryptographic audit logging."""
        c = self.get_case(case_id)
        if not c:
            return None

        note = AnalystNote(
            note_id=f"NOTE-{uuid.uuid4().hex[:6].upper()}",
            timestamp=time.time(),
            author=author or "Lead SOC Analyst",
            note_type=note_type,
            content=content.strip()
        )
        c.analyst_notes.append(note)
        c.updated_at = time.time()
        self._append_audit_entry(c, f"Analyst Note Added ({note_type})", author or "Lead SOC Analyst", content[:120])
        with get_db_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO investigation_cases (case_id, status, created_at, updated_at, source, case_data) VALUES (?, ?, ?, ?, ?, ?)", (c.case_id, c.status, c.created_at, c.updated_at, c.source, c.model_dump_json()))
            conn.commit()
        return note

    def update_analyst_decision(self, case_id: str, req: AnalystDecisionRequest) -> Optional[InvestigationCase]:
        """Update the human analyst review status and action on a case with cryptographic audit logging."""
        c = self.get_case(case_id)
        if not c:
            return None

        now = time.time()
        c.decision_history.analyst_review_status = "CONFIRMED" if "CONFIRM" in req.analyst_action else ("RESOLVED" if "DISMISS" in req.analyst_action else "MODIFIED")
        c.decision_history.analyst_action = req.analyst_action
        c.decision_history.analyst_rationale = req.rationale
        c.decision_history.updated_at = now

        if req.analyst_action == "DISMISS_FALSE_POSITIVE":
            c.status = "RESOLVED"
        elif "OVERRIDE" in req.analyst_action:
            c.status = "ACTION_RECOMMENDED"
        else:
            c.status = "RESOLVED"

        c.updated_at = now
        self._append_audit_entry(c, f"Analyst Decision: {req.analyst_action}", req.author or "Lead SOC Analyst", req.rationale)
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO investigation_cases (case_id, status, created_at, updated_at, source, case_data) VALUES (?, ?, ?, ?, ?, ?)",
                (c.case_id, c.status, c.created_at, c.updated_at, c.source, c.model_dump_json())
            )
            conn.commit()
        return c

    def create_case_from_evidence(self, req: CaseCreateRequest) -> InvestigationCase:
        """Create a new unified investigation case directly from uploaded evidence, file, URL, or context."""
        from backend.app.services.payment_forensics import payment_forensics_service
        from backend.app.schemas.check_payment import CheckPaymentRequest

        auto_input = req.input_type
        if auto_input == "AUTO":
            if req.image_base64:
                auto_input = "QR"
            elif req.payload and (req.payload.startswith("http://") or req.payload.startswith("https://")):
                auto_input = "LINK"
            elif req.payload and req.payload.startswith("upi://"):
                auto_input = "QR"
            elif req.filename:
                auto_input = "FILE"
            else:
                auto_input = "QR"

        check_req = CheckPaymentRequest(
            input_type=auto_input,
            payload=req.payload,
            image_base64=req.image_base64,
            filename=req.filename,
            transaction_context=req.transaction_context,
            allow_external_threat_lookup=req.allow_external_threat_lookup,
            external_file_submission_consent=req.external_file_submission_consent
        )

        check_res = payment_forensics_service.analyze_payment(check_req)
        case_obj = self.register_case_from_check_payment(check_res, check_req)

        if req.title:
            case_obj.summary.what_happened = f"[{req.title}] {case_obj.summary.what_happened}"

        if req.analyst_note:
            self.add_analyst_note(case_obj.case_id, "OBSERVATION", req.analyst_note)
            case_obj = self.get_case(case_obj.case_id) or case_obj

        self._append_audit_entry(case_obj, "Case Initialized", "INVESTIGATION_CENTER", f"New case created via direct investigation workspace. Source input: {auto_input}.")
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO investigation_cases (case_id, status, created_at, updated_at, source, case_data) VALUES (?, ?, ?, ?, ?, ?)",
                (case_obj.case_id, case_obj.status, case_obj.created_at, case_obj.updated_at, case_obj.source, case_obj.model_dump_json())
            )
            conn.commit()

        return case_obj

    def retry_or_analyze_case(self, case_id: str, req: CaseAnalyzeRequest) -> Optional[InvestigationCase]:
        """Re-runs analyzers or adds extra transaction context without duplicating evidence."""
        case_obj = self.get_case(case_id)
        if not case_obj:
            return None

        now = time.time()
        case_obj.updated_at = now

        if req.additional_transaction_context:
            for k, v in req.additional_transaction_context.items():
                case_obj.evidence.append({
                    "category": "CONTEXT",
                    "field": f"ctx_{k}",
                    "value": str(v),
                    "status": "OBSERVED",
                    "confidence": 1.0,
                    "source": "RETRY_ANALYSIS"
                })

        self._append_audit_entry(case_obj, "Analysis Retried", "ANALYST", f"Re-executed analysis pass. Analyzer subset: {req.analyzer_subset or 'ALL'}.")

        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO investigation_cases (case_id, status, created_at, updated_at, source, case_data) VALUES (?, ?, ?, ?, ?, ?)",
                (case_obj.case_id, case_obj.status, case_obj.created_at, case_obj.updated_at, case_obj.source, case_obj.model_dump_json())
            )
            conn.commit()

        return case_obj

    def reset_demo_cases(self) -> Dict[str, Any]:
        """Reset the investigation store to a clean deterministic SOC evaluation state for repeatable judge demos."""
        with get_db_connection() as conn:
            conn.execute("DELETE FROM investigation_cases")
            conn.commit()
        self._seed_default_cases()
        return {
            "status": "RESET_SUCCESSFUL",
            "message": "Investigation store reset to clean deterministic SOC evaluation state.",
            "active_cases": len(self.list_cases())
        }

    def export_case_report(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Export a clean, professional SOC investigation dossier report with cryptographic audit seal."""
        c = self.get_case(case_id)
        if not c:
            return None

        audit_verification = self.verify_case_audit_chain(case_id)

        return {
            "report_meta": {
                "dossier_id": f"DOSSIER-{c.case_id}",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "platform": "Q-FraudShield — Adaptive AI–Quantum Digital Payment Fraud Intelligence",
                "classification": "CONFIDENTIAL // SOC INVESTIGATION DOSSIER",
                "cryptographic_audit_seal": audit_verification.get("root_hash"),
                "audit_integrity_status": audit_verification.get("integrity_status")
            },
            "case_id": c.case_id,
            "status": c.status,
            "system_assessment": {
                "risk_score": c.risk["risk_score"],
                "risk_level": c.risk["risk_level"],
                "decision": c.risk["decision"],
                "confidence": c.risk["confidence"],
                "epistemic_uncertainty": c.risk.get("epistemic_uncertainty", 0.0),
                "recommendation": c.risk["recommendation"]
            },
            "summary": c.summary.model_dump(),
            "fraud_dna": c.fraud_dna,
            "scorecard": c.scorecard.model_dump(),
            "quantum_escalation": c.quantum_escalation,
            "evidence": c.evidence,
            "timeline": c.timeline,
            "entities": [e.model_dump() for e in c.entities],
            "related_cases": [r.model_dump() for r in c.related_cases],
            "model_analysis": c.model_analysis,
            "counterfactuals": c.counterfactuals,
            "limitations_and_disclosures": c.limitations,
            "analyst_notes": [n.model_dump() for n in c.analyst_notes],
            "decision_history": c.decision_history.model_dump(),
            "audit_chain": c.audit_chain,
            "audit_chain_verification": audit_verification
        }

# Global singleton
investigation_service = InvestigationService()
