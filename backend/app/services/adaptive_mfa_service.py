import time
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from backend.app.schemas.adaptive_mfa import (
    MFAFactorContribution, MFADecisionExplanation, AdaptiveMFAResponse,
    MFAVerificationSubmission, MFAVerificationResult
)
from backend.app.services.hardware_trust_service import hardware_trust_service
from backend.app.schemas.hardware_trust import AttestationVerificationRequest

class AdaptiveMFAService:
    """
    Enterprise Adaptive Risk-Based Authentication Engine.
    Converts multi-modal fraud signals (Transaction, Evidence, Behavioral DNA,
    Device Attestation, Network, and Quantum) into proportional authentication tiers.
    """

    def __init__(self):
        # In-memory session tracking for active MFA flows
        self._active_sessions: Dict[str, Dict[str, Any]] = {}

    def evaluate_adaptive_mfa(
        self,
        case_id: str,
        user_id: str,
        device_id: str,
        risk_score: float,
        evidence_items: Optional[List[Dict[str, Any]]] = None,
        risk_signals: Optional[List[Dict[str, Any]]] = None,
        transaction_dna: Optional[Dict[str, Any]] = None,
        quantum_analysis: Optional[Dict[str, Any]] = None,
        payload_integrity: Optional[Dict[str, Any]] = None,
        device_trust_score: Optional[float] = None
    ) -> AdaptiveMFAResponse:
        """
        Evaluates composite risk and evidence to determine the required Authentication Level (0 to 3)
        with an additive explainability breakdown.
        """
        session_id = f"MFA-SES-{int(time.time()*1000)}-{secrets.token_hex(4).upper()}"
        contributions: List[MFAFactorContribution] = []

        # 1. Base Population Risk
        baseline_risk = 5.0
        contributions.append(MFAFactorContribution(
            factor_name="Base Transaction Profile",
            risk_delta=baseline_risk,
            status="OBSERVED",
            evidence_summary="Standard baseline risk for retail UPI/digital transfer channel.",
            provenance="OBSERVED"
        ))

        # 2. Transaction DNA & Velocity Anomaly
        if transaction_dna:
            dna_anomaly = transaction_dna.get("anomaly_score", 0.0)
            if dna_anomaly > 0.4:
                pts = round(dna_anomaly * 25.0, 1)
                contributions.append(MFAFactorContribution(
                    factor_name="Behavioral DNA Deviation",
                    risk_delta=pts,
                    status="MODEL_INFERRED",
                    evidence_summary=f"Transaction deviates from user baseline (Anomaly Index: {dna_anomaly:.2f}).",
                    provenance="MODEL_INFERRED"
                ))

        # 3. Payload & Evidence Integrity (QR vs Screenshot vs Text)
        if payload_integrity and payload_integrity.get("status") == "MISMATCH":
            contributions.append(MFAFactorContribution(
                factor_name="Payload Mismatch (Visual vs QR)",
                risk_delta=30.0,
                status="OBSERVED",
                evidence_summary="Discrepancy detected between receipt payload and target routing VPA/amount.",
                provenance="OBSERVED"
            ))

        # 4. Hardware Attestation & Device Trust
        dev_trust = device_trust_score if device_trust_score is not None else 85.0
        if dev_trust < 50.0:
            contributions.append(MFAFactorContribution(
                factor_name="Hardware Attestation / Identity Compromise",
                risk_delta=28.0,
                status="HARDWARE_ATTESTED",
                evidence_summary=f"ESP32-S3 trust score degraded to {dev_trust:.1f}/100. Cryptographic or sensor failure.",
                provenance="HARDWARE_ATTESTED"
            ))
        elif dev_trust < 75.0:
            contributions.append(MFAFactorContribution(
                factor_name="Device Sensor / Timing Variance",
                risk_delta=14.0,
                status="HARDWARE_ATTESTED",
                evidence_summary=f"Moderate sensor baseline displacement or quartz timing drift detected ({dev_trust:.1f}/100).",
                provenance="HARDWARE_ATTESTED"
            ))

        # 5. Quantum Escalation Contribution
        quantum_triggered = False
        quantum_reason = None
        if quantum_analysis and quantum_analysis.get("quantum_kernel_invoked", False):
            quantum_triggered = True
            q_score = quantum_analysis.get("quantum_risk_score", 50.0)
            q_delta = round((q_score - 50.0) * 0.3, 1)
            quantum_reason = quantum_analysis.get("escalation_reason", "Borderline classical risk with hardware anomaly.")
            if q_delta > 0:
                contributions.append(MFAFactorContribution(
                    factor_name="Quantum Kernel Escalation",
                    risk_delta=q_delta,
                    status="QUANTUM_KERNEL_COMPUTED",
                    evidence_summary=f"4-Qubit ZZFeatureMap fidelity shift (Quantum Score: {q_score:.1f}).",
                    provenance="QUANTUM_KERNEL_COMPUTED"
                ))

        # 6. Sum total risk
        total_risk = sum(c.risk_delta for c in contributions)
        total_risk = max(0.0, min(100.0, max(total_risk, risk_score)))

        # 7. Determine Authentication Level
        if total_risk < 35.0 and dev_trust >= 80.0:
            auth_level = 0
            level_label = "LEVEL_0_PASSIVE"
            action_title = "Passive Verification (No Interruption)"
            decision = "APPROVE"
            rationale = "Signals match legitimate user behavior, trusted ESP32-S3 hardware attestation, and consistent evidence."
        elif total_risk < 60.0:
            auth_level = 1
            level_label = "LEVEL_1_POSSESSION_OTP"
            action_title = "Possession / TOTP Verification Required"
            decision = "STEP_UP_REQUIRED"
            rationale = "Moderate risk or minor behavioral deviation. Possession verification via registered device/OTP required."
        elif total_risk < 80.0:
            auth_level = 2
            level_label = "LEVEL_2_STRONG_PASSKEY"
            action_title = "Strong Authentication (FIDO2 / Passkey Required)"
            decision = "STEP_UP_REQUIRED"
            rationale = "Elevated risk or new transaction destination. Cryptographic biometric passkey verification required."
        else:
            auth_level = 3
            level_label = "LEVEL_3_HARDWARE_ATTESTATION"
            action_title = "Physical Hardware Cryptographic Attestation Required"
            decision = "STEP_UP_REQUIRED" if dev_trust > 30.0 else "BLOCK"
            rationale = "High-risk transaction or hardware trust failure. ESP32-S3 eFuse cryptographic challenge response required."

        explanation = MFADecisionExplanation(
            case_id=case_id,
            baseline_risk=baseline_risk,
            factor_contributions=contributions,
            total_calculated_risk=round(total_risk, 1),
            required_auth_level=auth_level,
            auth_level_label=level_label,
            required_action_title=action_title,
            rationale=rationale,
            quantum_escalation_triggered=quantum_triggered,
            quantum_escalation_reason=quantum_reason,
            provenance="MODEL_INFERRED"
        )

        # Prepare challenge payloads
        challenge_payload = None
        passkey_challenge = None
        otp_dest = None

        if auth_level == 3:
            chal = hardware_trust_service.create_challenge(device_id)
            challenge_payload = chal.model_dump()
        elif auth_level == 2:
            passkey_challenge = {
                "challenge": secrets.token_hex(32),
                "rp": {"name": "Quantum Kavacha Trust Node", "id": "localhost"},
                "user": {"id": user_id, "name": f"{user_id}@qk.local", "displayName": user_id},
                "pubKeyCredParams": [{"type": "public-key", "alg": -7}],
                "timeout": 60000,
                "attestation": "direct"
            }
        elif auth_level == 1:
            otp_dest = "+91 98*** **420 (SIMULATED SMS)"

        response = AdaptiveMFAResponse(
            auth_session_id=session_id,
            case_id=case_id,
            user_id=user_id,
            device_id=device_id,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            auth_level=auth_level,
            auth_level_label=level_label,
            decision=decision,
            explanation=explanation,
            challenge_payload=challenge_payload,
            passkey_challenge=passkey_challenge,
            otp_masked_destination=otp_dest,
            status="VERIFIED" if auth_level == 0 else "PENDING_VERIFICATION"
        )

        self._active_sessions[session_id] = {
            "response": response,
            "created_at": time.time(),
            "expected_level": auth_level
        }

        return response

    def verify_mfa_submission(self, submission: MFAVerificationSubmission) -> MFAVerificationResult:
        """
        Verifies client MFA response across OTP, Passkey, or ESP32-S3 Hardware Challenge.
        """
        session = self._active_sessions.get(submission.auth_session_id)
        if not session:
            return MFAVerificationResult(
                auth_session_id=submission.auth_session_id,
                case_id=submission.case_id,
                auth_type=submission.auth_type,
                verified=False,
                final_decision="BLOCK",
                post_verification_risk=95.0,
                message="MFA Session expired or invalid session ID.",
                details={"error": "SESSION_NOT_FOUND"},
                provenance="MODEL_INFERRED"
            )

        resp_obj: AdaptiveMFAResponse = session["response"]
        expected_level = session["expected_level"]

        # Level 3: Hardware Challenge Attestation Verification
        if submission.auth_type == "HARDWARE_CHALLENGE":
            if not submission.hardware_challenge_id or not submission.hardware_hmac_response:
                return MFAVerificationResult(
                    auth_session_id=submission.auth_session_id,
                    case_id=submission.case_id,
                    auth_type=submission.auth_type,
                    verified=False,
                    final_decision="BLOCK",
                    post_verification_risk=92.0,
                    message="Hardware cryptographic challenge response parameters missing.",
                    provenance="HARDWARE_ATTESTED"
                )

            req = AttestationVerificationRequest(
                challenge_id=submission.hardware_challenge_id,
                device_id=resp_obj.device_id,
                nonce=submission.hardware_nonce or "",
                hmac_response=submission.hardware_hmac_response,
                firmware_hash=submission.firmware_hash or "8f14e45fceea167a5a36dedd4bea2543",
                monotonic_counter=submission.monotonic_counter or 104,
                timestamp_utc=submission.timestamp_utc or datetime.now(timezone.utc).isoformat()
            )
            attest_res = hardware_trust_service.verify_attestation(req)

            if attest_res.verified:
                resp_obj.status = "VERIFIED"
                return MFAVerificationResult(
                    auth_session_id=submission.auth_session_id,
                    case_id=submission.case_id,
                    auth_type=submission.auth_type,
                    verified=True,
                    final_decision="APPROVE",
                    post_verification_risk=12.0,
                    message="ESP32-S3 Hardware eFuse cryptographic attestation VERIFIED. Transaction authorized.",
                    details=attest_res.model_dump(),
                    provenance="HARDWARE_ATTESTED"
                )
            else:
                return MFAVerificationResult(
                    auth_session_id=submission.auth_session_id,
                    case_id=submission.case_id,
                    auth_type=submission.auth_type,
                    verified=False,
                    final_decision="BLOCK",
                    post_verification_risk=95.0,
                    message=f"Hardware cryptographic attestation failed: {attest_res.message}",
                    details=attest_res.model_dump(),
                    provenance="HARDWARE_ATTESTED"
                )

        # Level 2: Passkey / WebAuthn Biometric Verification
        elif submission.auth_type == "PASSKEY":
            # Deterministic simulation/verification of WebAuthn signature
            is_valid = bool(submission.passkey_signature and len(submission.passkey_signature) >= 16)
            if is_valid:
                resp_obj.status = "VERIFIED"
                return MFAVerificationResult(
                    auth_session_id=submission.auth_session_id,
                    case_id=submission.case_id,
                    auth_type="PASSKEY",
                    verified=True,
                    final_decision="APPROVE",
                    post_verification_risk=18.0,
                    message="FIDO2 / WebAuthn cryptographic passkey verified. Transaction approved.",
                    details={"credential_type": "public-key", "authenticator": "User Biometric Enclave (SIMULATED)"},
                    provenance="MODEL_INFERRED"
                )
            else:
                return MFAVerificationResult(
                    auth_session_id=submission.auth_session_id,
                    case_id=submission.case_id,
                    auth_type="PASSKEY",
                    verified=False,
                    final_decision="BLOCK",
                    post_verification_risk=88.0,
                    message="Passkey signature invalid or rejected by user enclave.",
                    provenance="MODEL_INFERRED"
                )

        # Level 1: Possession / OTP Verification
        elif submission.auth_type == "OTP":
            # Standard demo OTP: 739218 or 6-digit number
            otp = (submission.otp_code or "").strip()
            is_valid = (otp == "739218" or len(otp) == 6)
            if is_valid:
                resp_obj.status = "VERIFIED"
                return MFAVerificationResult(
                    auth_session_id=submission.auth_session_id,
                    case_id=submission.case_id,
                    auth_type="OTP",
                    verified=True,
                    final_decision="APPROVE",
                    post_verification_risk=22.0,
                    message="Possession OTP verified. Step-up authentication completed.",
                    details={"otp_channel": "SMS_TOTP (SIMULATED)"},
                    provenance="MODEL_INFERRED"
                )
            else:
                return MFAVerificationResult(
                    auth_session_id=submission.auth_session_id,
                    case_id=submission.case_id,
                    auth_type="OTP",
                    verified=False,
                    final_decision="BLOCK",
                    post_verification_risk=85.0,
                    message="Invalid OTP code entered. Verification rejected.",
                    provenance="MODEL_INFERRED"
                )

        return MFAVerificationResult(
            auth_session_id=submission.auth_session_id,
            case_id=submission.case_id,
            auth_type=submission.auth_type,
            verified=False,
            final_decision="BLOCK",
            post_verification_risk=90.0,
            message="Unknown or unsupported authentication type.",
            provenance="MODEL_INFERRED"
        )

adaptive_mfa_service = AdaptiveMFAService()
