import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.app.schemas.response import (
    ResponseCenterData, ResponseRecommendation, ActionCard,
    PlaybookStep, EvidencePackage, EvidencePackageItem,
    ActionAuditEntry, SimpleViewGuide
)
from backend.app.schemas.investigation import InvestigationCase

class ResponseService:
    """
    Response Center + Report & Recover Service for Q-FraudShield (Phase 8).
    
    Transforms detection telemetry and case evidence into clear, evidence-grounded
    response recommendations, action playbooks, structured evidence dossiers,
    and verified audit trails.
    
    Core Principles:
    - Reuses authoritative risk score from risk_fusion_service.
    - Strictly separates RISK (how suspicious), CONFIDENCE (how strong evidence is),
      and ACTION (what should be considered next).
    - Clear distinction between USER ACTIONS, RECOMMENDED ACTIONS, SIMULATED ACTIONS,
      and EXTERNAL ACTIONS. Never claims Q-FraudShield directly frozen bank accounts.
    - Honest epistemic provenance: OBSERVED, INFERRED, UNAVAILABLE, DEMO / SYNTHETIC.
    """

    def __init__(self):
        # Case audit action store: case_id -> List[ActionAuditEntry]
        self._action_audits: Dict[str, List[ActionAuditEntry]] = {}

    def get_or_create_audit_trail(self, case: InvestigationCase) -> List[ActionAuditEntry]:
        """Retrieve real session audit trail or initialize baseline events based on case timeline."""
        if case.case_id in self._action_audits:
            return self._action_audits[case.case_id]

        # Initialize realistic baseline audit trail from case events
        created_dt = datetime.fromtimestamp(case.created_at, timezone.utc)
        trail: List[ActionAuditEntry] = [
            ActionAuditEntry(
                entry_id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
                timestamp=case.created_at,
                timestamp_formatted=created_dt.strftime("%H:%M:%S UTC"),
                action_name="System Risk Assessment Generated",
                actor="SYSTEM",
                details=f"Calculated risk score {case.risk.get('risk_score', 0):.1f}% with confidence {case.risk.get('confidence', 0.85):.2f}.",
                provenance="SYSTEM_GENERATED"
            )
        ]

        if case.quantum_escalation and case.quantum_escalation.get("quantum_execution_required"):
            q_time = case.created_at + 2
            q_dt = datetime.fromtimestamp(q_time, timezone.utc)
            trail.append(ActionAuditEntry(
                entry_id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
                timestamp=q_time,
                timestamp_formatted=q_dt.strftime("%H:%M:%S UTC"),
                action_name="Quantum Gate Escalation Executed",
                actor="SYSTEM",
                details="Evaluated 4-qubit non-linear kernel state to resolve feature ambiguity.",
                provenance="SYSTEM_GENERATED"
            ))

        # Add notes as audit entries if present
        for note in case.analyst_notes:
            n_dt = datetime.fromtimestamp(note.timestamp, timezone.utc)
            trail.append(ActionAuditEntry(
                entry_id=f"AUD-{note.note_id}",
                timestamp=note.timestamp,
                timestamp_formatted=n_dt.strftime("%H:%M:%S UTC"),
                action_name=f"Analyst Note Recorded ({note.note_type})",
                actor="ANALYST",
                details=note.content[:120] + ("..." if len(note.content) > 120 else ""),
                provenance="OBSERVED"
            ))

        # Add analyst decision if present
        if case.decision_history.analyst_action:
            d_dt = datetime.fromtimestamp(case.decision_history.updated_at, timezone.utc)
            trail.append(ActionAuditEntry(
                entry_id=f"AUD-DEC-{uuid.uuid4().hex[:6].upper()}",
                timestamp=case.decision_history.updated_at,
                timestamp_formatted=d_dt.strftime("%H:%M:%S UTC"),
                action_name=f"Analyst Review Submitted: {case.decision_history.analyst_action}",
                actor="ANALYST",
                details=f"Review status set to {case.decision_history.analyst_review_status}. Rationale: {case.decision_history.analyst_rationale or 'N/A'}",
                provenance="OBSERVED"
            ))

        self._action_audits[case.case_id] = trail
        return trail

    def record_audit_action(self, case_id: str, action_name: str, actor: str, details: str) -> ActionAuditEntry:
        """Record an explicit user/analyst action into the case audit trail."""
        now = time.time()
        dt_str = datetime.fromtimestamp(now, timezone.utc).strftime("%H:%M:%S UTC")
        entry = ActionAuditEntry(
            entry_id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            timestamp_formatted=dt_str,
            action_name=action_name,
            actor=actor,
            details=details,
            provenance="OBSERVED"
        )
        if case_id not in self._action_audits:
            self._action_audits[case_id] = []
        self._action_audits[case_id].append(entry)
        return entry

    def generate_response_center_data(self, case: InvestigationCase) -> ResponseCenterData:
        """
        Generate complete response center recommendations, playbook,
        evidence package, and guidance for a given investigation case.
        """
        risk_score = float(case.risk.get("risk_score", 50.0))
        confidence = float(case.risk.get("confidence", 0.85))
        ev_quality = case.scorecard.evidence_quality if case.scorecard else "HIGH"

        # Determine if compromise is suspected (device anomaly high + velocity burst + critical risk)
        is_compromise_suspected = False
        if risk_score >= 88.0:
            for entity in case.entities:
                if entity.entity_type == "DEVICE" and entity.risk_score >= 80.0:
                    is_compromise_suspected = True
                    break

        # 1. Determine Response Recommendation & Level
        if is_compromise_suspected or risk_score >= 90.0:
            rec = ResponseRecommendation(
                primary_action="DO NOT PAY & SECURE ACCOUNT",
                primary_action_code="SECURE_ACCOUNT",
                headline="Critical Threat & Potential Account Compromise",
                rationale="Severe forensic divergence, anomalous device profile, and high risk indicator detected. Payment should be stopped immediately and credentials secured.",
                risk_level="CRITICAL",
                risk_score=risk_score,
                confidence_score=confidence,
                confidence_level="HIGH" if confidence >= 0.8 else ("MEDIUM" if confidence >= 0.6 else "LOW"),
                evidence_quality=ev_quality,
                verification_recommendation="DO_NOT_PROCEED",
                verification_rationale="Authentication not advised until payee authenticity and device integrity are confirmed out-of-band.",
                is_compromise_suspected=True
            )
        elif risk_score >= 70.0:
            rec = ResponseRecommendation(
                primary_action="DO NOT PAY",
                primary_action_code="DO_NOT_PAY",
                headline="High Risk — Strong Indicator of Fraud or Phishing",
                rationale="Multiple independent signals indicate this payment request is deceptive or directed to an unverified recipient.",
                risk_level="HIGH",
                risk_score=risk_score,
                confidence_score=confidence,
                confidence_level="HIGH" if confidence >= 0.8 else ("MEDIUM" if confidence >= 0.6 else "LOW"),
                evidence_quality=ev_quality,
                verification_recommendation="STRONG_VERIFICATION",
                verification_rationale="Requires independent multi-channel verification and out-of-band payee confirmation before any funds transfer.",
                is_compromise_suspected=False
            )
        elif risk_score >= 40.0:
            rec = ResponseRecommendation(
                primary_action="REVIEW BEFORE PROCEEDING",
                primary_action_code="REVIEW_BEFORE_PROCEEDING",
                headline="Elevated Caution — Secondary Verification Advised",
                rationale="Partial anomaly observed. Payee identity or payment link requires confirmation before authorizing transfer.",
                risk_level="MEDIUM",
                risk_score=risk_score,
                confidence_score=confidence,
                confidence_level="HIGH" if confidence >= 0.8 else ("MEDIUM" if confidence >= 0.6 else "LOW"),
                evidence_quality=ev_quality,
                verification_recommendation="STEP_UP_VERIFICATION",
                verification_rationale="Biometric challenge or multi-factor confirmation recommended to ensure session intent.",
                is_compromise_suspected=False
            )
        else:
            rec = ResponseRecommendation(
                primary_action="PROCEED WITH NORMAL CAUTION",
                primary_action_code="PROCEED_WITH_CAUTION",
                headline="Low Risk — Consistent Payment Parameters",
                rationale="Standard payment signals verified. Note: No digital payment can be certified 100% risk-free.",
                risk_level="LOW",
                risk_score=risk_score,
                confidence_score=confidence,
                confidence_level="HIGH" if confidence >= 0.8 else ("MEDIUM" if confidence >= 0.6 else "LOW"),
                evidence_quality=ev_quality,
                verification_recommendation="NORMAL_VERIFICATION",
                verification_rationale="Standard banking authentication flow is sufficient.",
                is_compromise_suspected=False
            )

        # 2. Action Cards
        action_cards = self._build_action_cards(case, rec)

        # 3. Response Playbook
        playbook = self._build_playbook(case, rec)

        # 4. Report & Recover Evidence Package
        evidence_package = self._build_evidence_package(case)

        # 5. Audit Trail
        audit_trail = self.get_or_create_audit_trail(case)

        # 6. Simple View Guide
        simple_guide = self._build_simple_guide(case, rec)

        # 7. Limitations
        limitations = list(case.limitations) if case.limitations else [
            "Telecommunications SS7 routing metadata unavailable in current sandbox feed.",
            "External inter-bank credit bureau blacklist not queried directly; score is based on transaction telemetry and graph topology.",
            "All suggested actions are defensive recommendations; Q-FraudShield does not control bank-side settlement holds."
        ]

        return ResponseCenterData(
            case_id=case.case_id,
            risk_score=risk_score,
            confidence=confidence,
            evidence_quality=ev_quality,
            recommendation=rec,
            action_cards=action_cards,
            playbook=playbook,
            evidence_package=evidence_package,
            audit_trail=audit_trail,
            analyst_decision=case.decision_history.model_dump() if case.decision_history else None,
            simple_view_guide=simple_guide,
            limitations=limitations
        )

    def _build_action_cards(self, case: InvestigationCase, rec: ResponseRecommendation) -> List[ActionCard]:
        cards: List[ActionCard] = []

        # STOP PAYMENT
        if rec.risk_level in ["HIGH", "CRITICAL"]:
            cards.append(ActionCard(
                id="ACT-STOP-PAYMENT",
                title="STOP PAYMENT",
                description="Do not authorize or complete the transaction while the case has unresolved high-risk signals.",
                action_type="RECOMMENDED",
                status="RECOMMENDED",
                why=f"Overall risk score of {rec.risk_score:.1f}% indicates high probability of fraudulent diversion or deceptive payee.",
                evidence_grounding=[f"Risk score: {rec.risk_score:.1f}%", f"Decision: {case.risk.get('decision', 'BLOCK')}"],
                action_button_label="Don't Pay — View Next Steps",
                is_simulated=False,
                disclaimer="User action: Prevent payment in your banking or UPI application."
            ))
        elif rec.risk_level == "MEDIUM":
            cards.append(ActionCard(
                id="ACT-HOLD-REVIEW",
                title="PAUSE & REVIEW",
                description="Hold payment authorization until invoice details and recipient credentials are confirmed.",
                action_type="RECOMMENDED",
                status="RECOMMENDED",
                why="Moderate risk score indicates ambiguity in recipient VPA or unverified payment link.",
                evidence_grounding=[f"Risk score: {rec.risk_score:.1f}%"],
                action_button_label="Review Recommended Action",
                is_simulated=False
            ))

        # VERIFY RECIPIENT
        cards.append(ActionCard(
            id="ACT-VERIFY-RECIPIENT",
            title="VERIFY RECIPIENT",
            description="Confirm payee name and VPA directly with the intended beneficiary via trusted phone call or official app.",
            action_type="USER_ACTION",
            status="RECOMMENDED" if rec.risk_level != "LOW" else "OPTIONAL",
            why="Payee handle may be impersonating a legitimate merchant or company.",
            evidence_grounding=[f"Payee handle: {case.summary.what_happened if case.summary else 'N/A'}"],
            action_button_label="Verify Through Official App",
            is_simulated=False,
            disclaimer="Contact the recipient using a known contact number, never the number on the suspicious bill."
        ))

        # PRESERVE EVIDENCE
        cards.append(ActionCard(
            id="ACT-PRESERVE-EVIDENCE",
            title="PRESERVE EVIDENCE",
            description="Archive QR code payload, screenshot OCR text, payment link, and forensic metadata for official reporting.",
            action_type="RECOMMENDED",
            status="RECOMMENDED",
            why="Digital artifacts and telemetry can be lost or deleted if not exported immediately.",
            evidence_grounding=[f"Total evidence items: {len(case.evidence)}"],
            action_button_label="Export Incident Evidence Dossier",
            is_simulated=False
        ))

        # SECURE ACCOUNT (if critical or high device anomaly)
        if rec.is_compromise_suspected or rec.risk_level == "CRITICAL":
            cards.append(ActionCard(
                id="ACT-SECURE-ACCOUNT",
                title="SECURE ACCOUNT CREDENTIALS",
                description="Change UPI PIN and banking password from a known trusted device if device takeover or credential theft is suspected.",
                action_type="RECOMMENDED",
                status="RECOMMENDED",
                why="Anomalous hardware fingerprint signature and high session urgency indicate possible device compromise.",
                evidence_grounding=["Anomalous device signature", "Off-peak velocity burst"],
                action_button_label="Review Security Checklist",
                is_simulated=False
            ))

        # CONTACT FINANCIAL INSTITUTION
        if rec.risk_level in ["MEDIUM", "HIGH", "CRITICAL"]:
            cards.append(ActionCard(
                id="ACT-CONTACT-BANK",
                title="CONTACT FINANCIAL INSTITUTION",
                description="Notify your issuing bank or payment service provider's official customer support line.",
                action_type="EXTERNAL_ACTION",
                status="PENDING",
                why="Alert your financial institution to monitor for unauthorized transaction attempts.",
                evidence_grounding=[f"Case ID: {case.case_id}"],
                action_button_label="Open Official Banking Portal",
                is_simulated=False,
                disclaimer="External action: Always call the phone number printed on the back of your official debit/credit card."
            ))

        # REPORT FRAUD (Official Cybercrime / NPCI)
        if rec.risk_level in ["HIGH", "CRITICAL"]:
            cards.append(ActionCard(
                id="ACT-REPORT-CYBERCRIME",
                title="REPORT FRAUD TO AUTHORITIES",
                description="File an official cyber fraud complaint with NPCI and the National Cyber Crime Reporting Portal (1930 / cybercrime.gov.in).",
                action_type="EXTERNAL_ACTION",
                status="PENDING",
                why="Official cyber incident reporting enables inter-bank beneficiary account freezing under regulatory mandates.",
                evidence_grounding=[f"Case ID: {case.case_id}", f"Risk score: {rec.risk_score:.1f}%"],
                action_button_label="Open Cybercrime Reporting Portal (External)",
                action_url="https://cybercrime.gov.in",
                is_simulated=False,
                disclaimer="External regulatory portal: Q-FraudShield prepares the evidence package for copy-pasting."
            ))

        # SIMULATED GATEWAY HOLD
        cards.append(ActionCard(
            id="ACT-SIMULATED-GATEWAY-HOLD",
            title="SIMULATED GATEWAY HOLD",
            description="Simulated 4-hour settlement hold instruction for downstream payment gateway testing.",
            action_type="SIMULATED",
            status="COMPLETED" if rec.risk_level in ["HIGH", "CRITICAL"] else "NOT_APPLICABLE",
            why="Demonstrates automated policy enforcement logic in non-production sandbox environments.",
            evidence_grounding=["Sandbox mock gateway integration"],
            action_button_label="Simulated Policy Applied",
            is_simulated=True,
            disclaimer="DEMO / SIMULATED: In a live enterprise deployment, this triggers a webhook to your payment gateway."
        ))

        return cards

    def _build_playbook(self, case: InvestigationCase, rec: ResponseRecommendation) -> List[PlaybookStep]:
        steps: List[PlaybookStep] = []

        if rec.risk_level in ["HIGH", "CRITICAL"]:
            steps.append(PlaybookStep(
                step_number=1,
                title="Stop the Payment",
                instruction="Do not click 'Pay', do not enter your UPI PIN, and cancel any pending authorization prompts.",
                why=f"High risk score ({rec.risk_score:.1f}%) and conflicting payee indicators.",
                evidence=f"Decision: {case.risk.get('decision', 'BLOCK')} | Risk Level: {rec.risk_level}",
                status="ACTION_RECOMMENDED",
                actor="USER"
            ))
            steps.append(PlaybookStep(
                step_number=2,
                title="Verify Recipient Independently",
                instruction="Contact the intended recipient via phone call using a known trusted number.",
                why="Deceptive lookalike domain or mismatched payee handle detected in the payload.",
                evidence="Payee handle conflicts with declared merchant entity.",
                status="ACTION_RECOMMENDED",
                actor="USER"
            ))
            steps.append(PlaybookStep(
                step_number=3,
                title="Preserve Evidence Package",
                instruction="Download and save the Q-FraudShield Incident Evidence Dossier containing QR parameters and screenshots.",
                why="Crucial for official cybercrime reporting and bank dispute arbitration.",
                evidence=f"Case ID: {case.case_id} ({len(case.evidence)} telemetry items)",
                status="ACTION_RECOMMENDED",
                actor="USER"
            ))
            steps.append(PlaybookStep(
                step_number=4,
                title="Review Account & Device Security",
                instruction="Inspect recent transactions for unauthorized activity and update your authentication credentials.",
                why="Anomalous hardware signature or off-peak burst patterns observed.",
                evidence="Device score and velocity burst indicators.",
                status="ACTION_RECOMMENDED",
                actor="USER"
            ))
            steps.append(PlaybookStep(
                step_number=5,
                title="Contact Official Financial Institution",
                instruction="Call your bank's official fraud helpline using the number on your physical card.",
                why="Alert bank to flag potential incoming debit attempts on your account.",
                evidence=f"Risk Score: {rec.risk_score:.1f}%",
                status="PENDING",
                actor="EXTERNAL"
            ))
            steps.append(PlaybookStep(
                step_number=6,
                title="Report Through Official Cyber Portal",
                instruction="Submit a complaint to the National Cyber Crime Reporting Portal (1930 / cybercrime.gov.in) with the exported dossier.",
                why="Enables law enforcement to flag fraudulent beneficiary accounts across banking networks.",
                evidence="Full forensic evidence package ready for export.",
                status="PENDING",
                actor="EXTERNAL"
            ))
        elif rec.risk_level == "MEDIUM":
            steps.append(PlaybookStep(
                step_number=1,
                title="Pause Payment Authorization",
                instruction="Take a moment to review the exact payee name and amount displayed in your UPI application.",
                why=f"Moderate risk score ({rec.risk_score:.1f}%) due to unverified links or novelty factors.",
                evidence="Secondary anomaly signals detected in transaction telemetry.",
                status="ACTION_RECOMMENDED",
                actor="USER"
            ))
            steps.append(PlaybookStep(
                step_number=2,
                title="Verify Payee Identity",
                instruction="Ensure the VPA handle belongs to the genuine merchant or contact.",
                why="Payee handle has limited historical transaction records.",
                evidence="Payee profile novelty score.",
                status="ACTION_RECOMMENDED",
                actor="USER"
            ))
            steps.append(PlaybookStep(
                step_number=3,
                title="Perform Step-Up Authentication",
                instruction="Use biometric or multi-factor verification if your banking app supports it.",
                why="Step-up authentication mitigates accidental authorization of spoofed requests.",
                evidence="Risk-based verification recommendation.",
                status="OPTIONAL",
                actor="USER"
            ))
        else:
            steps.append(PlaybookStep(
                step_number=1,
                title="Proceed with Standard Caution",
                instruction="Review the final payment summary screen in your banking application before confirming.",
                why="Telemetry parameters align with typical genuine merchant transactions.",
                evidence=f"Risk score: {rec.risk_score:.1f}% (Low Risk)",
                status="COMPLETED",
                actor="USER"
            ))
            steps.append(PlaybookStep(
                step_number=2,
                title="Verify Recipient Name on Screen",
                instruction="Ensure the recipient name displayed matches your intended beneficiary.",
                why="Good payment hygiene for all digital financial transfers.",
                evidence="Standard payment verification protocol.",
                status="OPTIONAL",
                actor="USER"
            ))

        return steps

    def _build_evidence_package(self, case: InvestigationCase) -> EvidencePackage:
        items: List[EvidencePackageItem] = []
        unavailable_fields: List[str] = []

        # 1. Case ID
        items.append(EvidencePackageItem(
            field_name="case_id",
            field_label="Case Identifier",
            value=case.case_id,
            provenance="OBSERVED",
            notes="Unique Q-FraudShield case record"
        ))

        # 2. Created Timestamp
        dt_str = datetime.fromtimestamp(case.created_at, timezone.utc).isoformat()
        items.append(EvidencePackageItem(
            field_name="timestamp",
            field_label="Detection Timestamp (UTC)",
            value=dt_str,
            provenance="OBSERVED"
        ))

        # 3. Transaction Amount & Currency
        amount_found = False
        for ev in case.evidence:
            if ev.get("field") == "amount" and ev.get("value") is not None:
                items.append(EvidencePackageItem(
                    field_name="amount",
                    field_label="Transaction Amount",
                    value=f"₹{ev['value']}",
                    provenance=ev.get("provenance", "OBSERVED")
                ))
                amount_found = True
                break
        if not amount_found:
            items.append(EvidencePackageItem(
                field_name="amount",
                field_label="Transaction Amount",
                value="[UNAVAILABLE in raw payload]",
                provenance="UNAVAILABLE"
            ))
            unavailable_fields.append("amount")

        # 4. Payee / Recipient
        recip_found = False
        for ent in case.entities:
            if ent.entity_type in ["RECIPIENT", "MERCHANT"]:
                items.append(EvidencePackageItem(
                    field_name="recipient_vpa",
                    field_label="Recipient Payee / VPA",
                    value=f"{ent.name} ({ent.entity_id})",
                    provenance=ent.status or "OBSERVED"
                ))
                recip_found = True
                break
        if not recip_found:
            items.append(EvidencePackageItem(
                field_name="recipient_vpa",
                field_label="Recipient Payee / VPA",
                value="[UNAVAILABLE]",
                provenance="UNAVAILABLE"
            ))
            unavailable_fields.append("recipient_vpa")

        # 5. Device Fingerprint
        dev_found = False
        for ent in case.entities:
            if ent.entity_type == "DEVICE":
                items.append(EvidencePackageItem(
                    field_name="device_fingerprint",
                    field_label="Originating Device ID",
                    value=ent.entity_id,
                    provenance=ent.status or "OBSERVED",
                    notes=f"Risk Score: {ent.risk_score}"
                ))
                dev_found = True
                break
        if not dev_found:
            items.append(EvidencePackageItem(
                field_name="device_fingerprint",
                field_label="Originating Device ID",
                value="[UNAVAILABLE]",
                provenance="UNAVAILABLE"
            ))
            unavailable_fields.append("device_fingerprint")

        # 6. Risk Score & Decision
        items.append(EvidencePackageItem(
            field_name="risk_score",
            field_label="Authoritative Risk Score",
            value=f"{case.risk.get('risk_score', 0):.1f}% ({case.risk.get('risk_level', 'UNKNOWN')})",
            provenance="OBSERVED",
            notes=f"Confidence: {case.risk.get('confidence', 0.85):.2f}"
        ))

        # 7. QR Payload / Link
        qr_found = False
        for ev in case.evidence:
            if "qr" in ev.get("field", "").lower() or "url" in ev.get("field", "").lower():
                items.append(EvidencePackageItem(
                    field_name="payment_artifact",
                    field_label="Extracted QR Payload / Link",
                    value=str(ev.get("value", "")),
                    provenance=ev.get("provenance", "OBSERVED")
                ))
                qr_found = True
                break
        if not qr_found:
            items.append(EvidencePackageItem(
                field_name="payment_artifact",
                field_label="Extracted QR Payload / Link",
                value="[UNAVAILABLE — Not an artifact-based input]",
                provenance="UNAVAILABLE"
            ))
            unavailable_fields.append("payment_artifact")

        # 8. External SS7 Telemetry (explicitly marked unavailable)
        items.append(EvidencePackageItem(
            field_name="ss7_telecom_routing",
            field_label="Carrier SS7 Location Feed",
            value="[UNAVAILABLE — Sandbox Mode without direct telco tie-in]",
            provenance="UNAVAILABLE",
            notes="Honest boundary disclosure"
        ))
        unavailable_fields.append("ss7_telecom_routing")

        # 9. FraudDNA Summary
        if case.fraud_dna and "axes" in case.fraud_dna:
            dna_drivers = []
            for k, ax in case.fraud_dna["axes"].items():
                if ax.get("score", 0) >= 70:
                    dna_drivers.append(f"{ax.get('axis_name', k)} ({ax.get('score')}%)")
            items.append(EvidencePackageItem(
                field_name="fraud_dna_primary_axes",
                field_label="FraudDNA Elevated Risk Axes",
                value=", ".join(dna_drivers) if dna_drivers else "None above 70%",
                provenance="INFERRED",
                notes="Synthesized from multi-signal feature attribution"
            ))

        # 10. Analyst Notes
        if case.analyst_notes:
            notes_str = "; ".join([f"[{n.note_type}] {n.content}" for n in case.analyst_notes])
            items.append(EvidencePackageItem(
                field_name="analyst_notes",
                field_label="SOC Analyst Investigation Notes",
                value=notes_str,
                provenance="OBSERVED"
            ))

        # Count provenance categories
        obs_count = sum(1 for i in items if i.provenance == "OBSERVED")
        inf_count = sum(1 for i in items if i.provenance == "INFERRED")
        una_count = sum(1 for i in items if i.provenance == "UNAVAILABLE")

        # Markdown summary
        md_lines = [
            f"### Q-FraudShield Incident Evidence Dossier: `{case.case_id}`",
            f"**Generated At**: {dt_str}",
            f"**Authoritative Risk Score**: {case.risk.get('risk_score', 0):.1f}% ({case.risk.get('risk_level', 'HIGH')})",
            f"**System Recommendation**: {case.risk.get('recommendation', 'DO NOT PAY')}",
            "",
            "#### Evidence Items Table:",
            "| Field | Value | Provenance | Notes |",
            "| :--- | :--- | :--- | :--- |"
        ]
        for it in items:
            val = str(it.value).replace("|", "/")
            md_lines.append(f"| {it.field_label} | `{val}` | **[{it.provenance}]** | {it.notes or ''} |")

        return EvidencePackage(
            case_id=case.case_id,
            generated_at=dt_str,
            items=items,
            summary_markdown="\n".join(md_lines),
            raw_evidence_count=len(items),
            observed_fields_count=obs_count,
            inferred_fields_count=inf_count,
            unavailable_fields_count=una_count,
            unavailable_fields=unavailable_fields
        )

    def _build_simple_guide(self, case: InvestigationCase, rec: ResponseRecommendation) -> SimpleViewGuide:
        if rec.risk_level in ["HIGH", "CRITICAL"]:
            return SimpleViewGuide(
                what_should_i_do="Do not pay. Stop this transaction immediately.",
                primary_recommendation="DO NOT PAY",
                why_explanation="Q-FraudShield detected strong evidence of deceptive payee details or fraudulent lookalike domain.",
                what_to_do_now=[
                    "Cancel or close the payment prompt in your banking app.",
                    "Save the payment link, QR code, or screenshot for records.",
                    "Verify the merchant or contact through their verified phone number."
                ],
                what_to_avoid=[
                    "Do not enter your UPI PIN or debit card OTP.",
                    "Do not call phone numbers listed inside suspicious emails or QR receipts.",
                    "Do not click secondary links sent by the requester."
                ],
                when_to_seek_help="If you already entered your PIN or money was debited, immediately call your bank's 24x7 fraud helpline and report to cybercrime.gov.in (dial 1930 in India).",
                checklist_status="CRITICAL_RISK_DETECTED"
            )
        elif rec.risk_level == "MEDIUM":
            return SimpleViewGuide(
                what_should_i_do="Pause and verify before completing payment.",
                primary_recommendation="REVIEW BEFORE PROCEEDING",
                why_explanation="Some transaction details appear unverified or unusual. Secondary confirmation is recommended.",
                what_to_do_now=[
                    "Double check the recipient name on your screen.",
                    "Confirm the payment amount is exact.",
                    "Contact the recipient out-of-band if this is your first time paying them."
                ],
                what_to_avoid=[
                    "Do not rush to pay without checking the account name.",
                    "Do not make split payments or follow urgent instructions from unfamiliar callers."
                ],
                when_to_seek_help="Contact customer care if the payment request claims to be an urgent bill from your utility provider or bank.",
                checklist_status="ELEVATED_RISK_DETECTED"
            )
        else:
            return SimpleViewGuide(
                what_should_i_do="Proceed with normal caution.",
                primary_recommendation="PROCEED WITH NORMAL CAUTION",
                why_explanation="Payment parameters match standard verified patterns. Always maintain standard digital safety hygiene.",
                what_to_do_now=[
                    "Review recipient name on the final payment confirmation screen.",
                    "Authorize transaction as normal."
                ],
                what_to_avoid=[
                    "Never share your UPI PIN or banking passwords with anyone."
                ],
                when_to_seek_help="If your bank ever contacts you asking for PINs, decline and call their official customer care.",
                checklist_status="STANDARD_VERIFIED"
            )

    def generate_forensic_report(self, case: InvestigationCase) -> Dict[str, Any]:
        """
        Build an exportable 11-section forensic case dossier compliant with Section 9.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        resp_data = self.generate_response_center_data(case)

        return {
            "1_case_overview": {
                "dossier_id": f"DOSSIER-{case.case_id}",
                "case_id": case.case_id,
                "status": case.status,
                "generated_at": now_iso,
                "classification": "CONFIDENTIAL // FINTECH SOC FRAUD DOSSIER",
                "source": case.source,
                "provenance": "OBSERVED"
            },
            "2_payment_details": {
                "summary": case.summary.what_happened,
                "risk_score": case.risk.get("risk_score"),
                "decision": case.risk.get("decision"),
                "provenance": "OBSERVED"
            },
            "3_risk_assessment": {
                "risk_score": case.risk.get("risk_score"),
                "risk_level": case.risk.get("risk_level"),
                "confidence": case.risk.get("confidence"),
                "epistemic_uncertainty": case.risk.get("epistemic_uncertainty", 0.0),
                "system_recommendation": case.risk.get("recommendation"),
                "provenance": "OBSERVED"
            },
            "4_evidence_summary": {
                "evidence_count": len(case.evidence),
                "evidence_items": case.evidence,
                "scorecard": case.scorecard.model_dump() if case.scorecard else {},
                "provenance": "OBSERVED"
            },
            "5_why_it_was_flagged": {
                "primary_risk_drivers": case.summary.primary_risk_drivers,
                "why_suspicious": case.summary.why_suspicious,
                "mitigating_factors": case.summary.mitigating_factors,
                "provenance": "INFERRED"
            },
            "6_fraud_dna": {
                "dna_structure": case.fraud_dna,
                "quantum_complexity": case.quantum_escalation,
                "provenance": "INFERRED"
            },
            "7_attack_chain": {
                "reconstructed_timeline": case.timeline,
                "provenance": "INFERRED"
            },
            "8_connected_entities": {
                "entities": [e.model_dump() for e in case.entities],
                "related_cases": [r.model_dump() for r in case.related_cases],
                "provenance": "OBSERVED"
            },
            "9_recommended_actions": {
                "primary_recommendation": resp_data.recommendation.model_dump(),
                "action_cards": [a.model_dump() for a in resp_data.action_cards],
                "playbook": [p.model_dump() for p in resp_data.playbook],
                "verification_recommendation": resp_data.recommendation.verification_recommendation,
                "provenance": "INFERRED"
            },
            "10_limitations": {
                "disclosures": resp_data.limitations,
                "boundary_notice": resp_data.boundary_disclaimer,
                "provenance": "EXPLICIT_DISCLOSURE"
            },
            "11_provenance": {
                "observed_fields_count": resp_data.evidence_package.observed_fields_count,
                "inferred_fields_count": resp_data.evidence_package.inferred_fields_count,
                "unavailable_fields_count": resp_data.evidence_package.unavailable_fields_count,
                "unavailable_fields": resp_data.evidence_package.unavailable_fields,
                "audit_trail_entries_count": len(resp_data.audit_trail),
                "audit_trail": [t.model_dump() for t in resp_data.audit_trail]
            }
        }

# Global singleton
response_service = ResponseService()
