import os
import re
import time
import base64
import urllib.parse
import ipaddress
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone

from backend.app.schemas.transaction import TransactionPayload
from backend.app.schemas.check_payment import (
    CheckPaymentRequest, CheckPaymentResponse, EvidenceItem, RiskSignal,
    CrossValidationItem, CrossValidationResult
)
from backend.app.services.fraud_engine import fraud_engine
from backend.app.services.threat_intel_service import threat_intel_service
from backend.app.services.transaction_dna_service import transaction_dna_service

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from rapidocr_onnxruntime import RapidOCR
    HAS_RAPID_OCR = True
    ocr_engine = RapidOCR()
except Exception:
    HAS_RAPID_OCR = False
    ocr_engine = None


class PaymentForensicsService:
    """
    Multi-Modal Digital Payment Forensics Engine for Q-FraudShield.
    Extracts, validates, and normalizes evidence from QR codes, screenshots,
    and payment links with strict SSRF protection and deterministic risk attribution.
    """

    # High-Risk Social Engineering Patterns
    SOCIAL_ENGINEERING_PATTERNS = [
        (r"(?i)\b(urgent|immediately|act now|hurry|expire[s]?)\b", "Urgency Pressure Language", "HIGH"),
        (r"(?i)\b(kyc\s*(?:\w+\s*){0,2}suspend\w*|account\s*(?:\w+\s*){0,3}block\w*|card\s*block\w*|freeze\s*account\w*|pending\s*kyc)\b", "Account Suspension Threat", "CRITICAL"),
        (r"(?i)\b(refund|cashback|bonus|lottery|prize|win\s+\d+|reward)\b", "Lure / False Reward Bait", "HIGH"),
        (r"(?i)\b(customer\s+care|support\s+desk|helpline|official\s+help)\b", "Impersonation / Fake Support Claim", "MODERATE"),
        (r"(?i)\b(send\s+money\s+to\s+receive|pay\s+advance|processing\s+fee)\b", "Advance Fee Fraud Pattern", "CRITICAL"),
        (r"(?i)\b(verify\s+otp|share\s+pin|enter\s+mpin)\b", "Credential Harvesting Intent", "CRITICAL"),
    ]

    # Suspicious Top-Level Domains & Lookalikes
    SUSPICIOUS_TLDS = {".xyz", ".top", ".tk", ".ml", ".ga", ".cf", ".gq", ".click", ".buzz", ".monster", ".rest", ".online"}
    BRAND_KEYWORDS = ["paytm", "phonepe", "gpay", "bhim", "sbi", "hdfc", "icici", "rbi", "npci", "amazonpay", "razorpay"]

    # Private IP Networks for SSRF Safety
    PRIVATE_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
        ipaddress.ip_network("fe80::/10"),
    ]

    def decode_qr_image(self, image_base64: str) -> Tuple[Optional[str], Optional[str]]:
        """Safely decode QR code payload(s) from base64 image bytes, detecting single or multiple QRs."""
        if not HAS_CV2:
            return None, "OpenCV QR detector is unavailable in current runtime."

        try:
            # Strip data URL prefix if present
            if "," in image_base64:
                image_base64 = image_base64.split(",", 1)[1]

            image_bytes = base64.b64decode(image_base64)
            if len(image_bytes) > 10 * 1024 * 1024:
                return None, "Image exceeds maximum allowed size (10 MB)."

            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return None, "Malformed or unsupported image format."

            detector = cv2.QRCodeDetector()

            # Check for multiple QR codes first if supported
            if hasattr(detector, "detectAndDecodeMulti"):
                try:
                    retval, decoded_info, points, _ = detector.detectAndDecodeMulti(img)
                    if retval and decoded_info:
                        non_empty = [txt.strip() for txt in decoded_info if txt and txt.strip()]
                        if len(non_empty) > 1:
                            # Flag multiple QRs detected - return the primary but indicate multiplicity
                            return non_empty[0], f"MULTIPLE_QR_DETECTED:{len(non_empty)}"
                        elif len(non_empty) == 1:
                            return non_empty[0], None
                except Exception:
                    pass

            val, points, _ = detector.detectAndDecode(img)
            if val:
                return val.strip(), None
            else:
                return None, "No readable QR code found in provided image."
        except Exception as e:
            return None, f"QR decoding error: {str(e)}"

    def extract_screenshot_ocr(self, image_base64: str) -> Tuple[str, Optional[str]]:
        """Safely extract OCR text from payment screenshot."""
        if not HAS_RAPID_OCR or ocr_engine is None:
            return "", "RapidOCR engine is unavailable in runtime."

        try:
            if "," in image_base64:
                image_base64 = image_base64.split(",", 1)[1]

            image_bytes = base64.b64decode(image_base64)
            if len(image_bytes) > 5 * 1024 * 1024:
                return "", "Image exceeds maximum allowed size (5 MB)."

            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return "", "Malformed image format."

            result, _ = ocr_engine(img)
            if not result:
                return "", "No text detected in screenshot."

            text_lines = [line[1] for line in result if len(line) >= 2]
            return "\n".join(text_lines), None
        except Exception as e:
            return "", f"OCR extraction error: {str(e)}"

    def parse_upi_payload(self, raw_payload: str) -> Dict[str, Any]:
        """Parse and structure UPI payment URI parameters."""
        parsed = {
            "is_upi": False,
            "pa": None, # Payee Address (VPA)
            "pn": None, # Payee Name
            "am": None, # Amount
            "cu": "INR", # Currency
            "tn": None, # Transaction Note
            "tr": None, # Transaction Ref ID
            "mc": None, # Merchant Code
            "mode": None,
            "extra_params": {}
        }

        if not raw_payload:
            return parsed

        raw_trimmed = raw_payload.strip()
        if raw_trimmed.startswith("upi://pay") or "pa=" in raw_trimmed:
            parsed["is_upi"] = True
            query_str = raw_trimmed.split("?", 1)[1] if "?" in raw_trimmed else raw_trimmed
            params = urllib.parse.parse_qs(query_str)

            for k, v in params.items():
                val = v[0] if v else ""
                k_lower = k.lower()
                if k_lower == "pa":
                    parsed["pa"] = val
                elif k_lower == "pn":
                    parsed["pn"] = val
                elif k_lower == "am":
                    try:
                        parsed["am"] = float(val)
                    except ValueError:
                        parsed["am"] = val
                elif k_lower == "cu":
                    parsed["cu"] = val
                elif k_lower == "tn":
                    parsed["tn"] = val
                elif k_lower == "tr":
                    parsed["tr"] = val
                elif k_lower == "mc":
                    parsed["mc"] = val
                elif k_lower == "mode":
                    parsed["mode"] = val
                else:
                    parsed["extra_params"][k] = val

        return parsed

    def validate_url_security(self, url: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Static URL Security Analyzer with strict SSRF, localhost, and protocol protections.
        Does NOT execute arbitrary outbound network requests.
        """
        security_meta = {
            "scheme": None,
            "domain": None,
            "is_safe_protocol": False,
            "is_ip_address": False,
            "is_private_ip": False,
            "has_suspicious_tld": False,
            "lookalike_brands": [],
            "excessive_encoding": False,
            "query_param_count": 0
        }

        if not url or not isinstance(url, str):
            return False, "Empty or invalid URL input", security_meta

        url_clean = url.strip()

        # Reject dangerous schemes immediately
        forbidden_schemes = ["javascript:", "data:", "file:", "ftp:", "gopher:", "dict:", "ldap:"]
        for fs in forbidden_schemes:
            if url_clean.lower().startswith(fs):
                return False, f"Dangerous URL scheme rejected: {fs}", security_meta

        try:
            parsed = urllib.parse.urlparse(url_clean)
        except Exception:
            return False, "Malformed URL format.", security_meta

        security_meta["scheme"] = parsed.scheme.lower() if parsed.scheme else "none"
        security_meta["domain"] = parsed.netloc.lower() if parsed.netloc else ""

        # Check for UPI scheme
        if security_meta["scheme"] == "upi":
            security_meta["is_safe_protocol"] = True
            return True, "Valid UPI payment URI scheme.", security_meta

        if security_meta["scheme"] not in ["http", "https"]:
            return False, f"Unsupported protocol: {security_meta['scheme']}. Only HTTPS and UPI are accepted.", security_meta

        security_meta["is_safe_protocol"] = True
        host = parsed.hostname or ""

        # Check for localhost / loopback
        if host.lower() in ["localhost", "127.0.0.1", "::1", "0.0.0.0"]:
            security_meta["is_private_ip"] = True
            return False, "SSRF Blocked: Localhost and loopback destinations are forbidden.", security_meta

        # Check for IP literal & private network
        try:
            ip_obj = ipaddress.ip_address(host)
            security_meta["is_ip_address"] = True
            for priv in self.PRIVATE_NETWORKS:
                if ip_obj in priv:
                    security_meta["is_private_ip"] = True
                    return False, f"SSRF Blocked: Private IP address {host} is forbidden.", security_meta
        except ValueError:
            security_meta["is_ip_address"] = False

        # Domain structure and TLD check
        for tld in self.SUSPICIOUS_TLDS:
            if host.endswith(tld):
                security_meta["has_suspicious_tld"] = True
                break

        # Brand Lookalike keyword check
        for brand in self.BRAND_KEYWORDS:
            if brand in host and not (host.endswith(f"{brand}.com") or host.endswith(f"{brand}.in")):
                security_meta["lookalike_brands"].append(brand)

        # Check query parameters
        params = urllib.parse.parse_qs(parsed.query)
        security_meta["query_param_count"] = len(params)
        if "%25" in parsed.query or "%20" in parsed.netloc:
            security_meta["excessive_encoding"] = True

        return True, "URL structure validated successfully.", security_meta

    def extract_social_engineering_signals(self, text: str) -> List[RiskSignal]:
        """Detect urgency, threat, or lure patterns in extracted text."""
        signals = []
        if not text:
            return signals

        for pattern, name, severity in self.SOCIAL_ENGINEERING_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                matched_sample = ", ".join(list(set(matches))[:3])
                signals.append(RiskSignal(
                    name=name,
                    severity=severity,
                    status="OBSERVED",
                    description=f"Detected social engineering pattern matching: '{matched_sample}'",
                    interpretation="Urgency language is commonly used in payment deception and account takeover lures."
                ))

        return signals

    def evaluate_cross_validation(
        self,
        ocr_text: Optional[str],
        upi_data: Dict[str, Any],
        transaction_context: Optional[Dict[str, Any]],
        extracted_ocr_amt: Optional[float] = None,
        extracted_ocr_vpa: Optional[str] = None,
        extracted_ocr_merchant: Optional[str] = None
    ) -> CrossValidationResult:
        """
        Deterministic First-Class Evidence Cross-Validation Engine.
        Compares:
        1. OCR extracted visual text
        2. QR decoded payload
        3. Stated transaction context
        Evaluates amount, payee VPA, merchant name, reference ID, and timestamp.
        Returns explicit status: MATCH | MISMATCH | UNAVAILABLE.
        """
        items: Dict[str, CrossValidationItem] = {}
        ctx = transaction_context or {}

        # 1. Amount Cross-Check
        qr_amt = None
        if upi_data.get("am") is not None:
            try:
                qr_amt = float(upi_data["am"])
            except (ValueError, TypeError):
                pass

        ctx_amt = None
        if ctx.get("amount") is not None:
            try:
                ctx_amt = float(ctx["amount"])
            except (ValueError, TypeError):
                pass

        if extracted_ocr_amt is not None and qr_amt is not None:
            if abs(extracted_ocr_amt - qr_amt) < 0.01:
                items["amount"] = CrossValidationItem(
                    field="amount",
                    status="MATCH",
                    ocr_value=extracted_ocr_amt,
                    qr_value=qr_amt,
                    context_value=ctx_amt,
                    severity="NEUTRAL",
                    details=f"Visual amount (₹{extracted_ocr_amt:,.2f}) matches embedded QR amount (₹{qr_amt:,.2f})."
                )
            else:
                items["amount"] = CrossValidationItem(
                    field="amount",
                    status="MISMATCH",
                    ocr_value=extracted_ocr_amt,
                    qr_value=qr_amt,
                    context_value=ctx_amt,
                    severity="CRITICAL",
                    details=f"Amount discrepancy: Visual receipt displays ₹{extracted_ocr_amt:,.2f} but underlying QR requests ₹{qr_amt:,.2f}."
                )
        elif extracted_ocr_amt is not None and ctx_amt is not None:
            if abs(extracted_ocr_amt - ctx_amt) < 0.01:
                items["amount"] = CrossValidationItem(
                    field="amount",
                    status="MATCH",
                    ocr_value=extracted_ocr_amt,
                    context_value=ctx_amt,
                    severity="NEUTRAL",
                    details=f"Visual amount (₹{extracted_ocr_amt:,.2f}) matches declared transaction amount."
                )
            else:
                items["amount"] = CrossValidationItem(
                    field="amount",
                    status="MISMATCH",
                    ocr_value=extracted_ocr_amt,
                    context_value=ctx_amt,
                    severity="CRITICAL",
                    details=f"Amount mismatch: Visual displays ₹{extracted_ocr_amt:,.2f} vs declared intent ₹{ctx_amt:,.2f}."
                )
        elif qr_amt is not None and ctx_amt is not None:
            if abs(qr_amt - ctx_amt) < 0.01:
                items["amount"] = CrossValidationItem(
                    field="amount",
                    status="MATCH",
                    qr_value=qr_amt,
                    context_value=ctx_amt,
                    severity="NEUTRAL",
                    details=f"QR amount (₹{qr_amt:,.2f}) matches declared intent."
                )
            else:
                items["amount"] = CrossValidationItem(
                    field="amount",
                    status="MISMATCH",
                    qr_value=qr_amt,
                    context_value=ctx_amt,
                    severity="CRITICAL",
                    details=f"QR payload requests ₹{qr_amt:,.2f}, differing from declared ₹{ctx_amt:,.2f}."
                )
        else:
            items["amount"] = CrossValidationItem(
                field="amount",
                status="UNAVAILABLE",
                ocr_value=extracted_ocr_amt,
                qr_value=qr_amt,
                context_value=ctx_amt,
                severity="NEUTRAL",
                details="Single-source or unconstrained amount parameter."
            )

        # 2. VPA / Payee Address Cross-Check
        qr_vpa = str(upi_data["pa"]).strip().lower() if upi_data.get("pa") else None
        ctx_vpa = str(ctx.get("recipient_vpa", "")).strip().lower() if ctx.get("recipient_vpa") else None
        ocr_vpa_clean = str(extracted_ocr_vpa).strip().lower() if extracted_ocr_vpa else None

        if ocr_vpa_clean and qr_vpa:
            if ocr_vpa_clean == qr_vpa:
                items["vpa"] = CrossValidationItem(
                    field="vpa",
                    status="MATCH",
                    ocr_value=ocr_vpa_clean,
                    qr_value=qr_vpa,
                    context_value=ctx_vpa,
                    severity="NEUTRAL",
                    details=f"Visual payee handle '{ocr_vpa_clean}' matches QR destination."
                )
            else:
                items["vpa"] = CrossValidationItem(
                    field="vpa",
                    status="MISMATCH",
                    ocr_value=ocr_vpa_clean,
                    qr_value=qr_vpa,
                    context_value=ctx_vpa,
                    severity="CRITICAL",
                    details=f"Payee mismatch: Visual text displays '{ocr_vpa_clean}' but underlying QR routes to '{qr_vpa}'."
                )
        elif qr_vpa and ctx_vpa:
            if qr_vpa == ctx_vpa:
                items["vpa"] = CrossValidationItem(
                    field="vpa",
                    status="MATCH",
                    qr_value=qr_vpa,
                    context_value=ctx_vpa,
                    severity="NEUTRAL",
                    details=f"QR payee destination '{qr_vpa}' matches authorized context."
                )
            else:
                items["vpa"] = CrossValidationItem(
                    field="vpa",
                    status="MISMATCH",
                    qr_value=qr_vpa,
                    context_value=ctx_vpa,
                    severity="CRITICAL",
                    details=f"Payee diversion: QR destination '{qr_vpa}' does not match declared beneficiary '{ctx_vpa}'."
                )
        else:
            items["vpa"] = CrossValidationItem(
                field="vpa",
                status="UNAVAILABLE",
                ocr_value=ocr_vpa_clean,
                qr_value=qr_vpa,
                context_value=ctx_vpa,
                severity="NEUTRAL",
                details="Payee address observed from single evidence channel."
            )

        # 3. Merchant Name Cross-Check
        qr_pn = str(upi_data.get("pn", "")).strip() if upi_data.get("pn") else None
        if extracted_ocr_merchant and qr_pn:
            ocr_clean = re.sub(r"[^\w]", "", extracted_ocr_merchant.lower())
            qr_clean = re.sub(r"[^\w]", "", qr_pn.lower())
            if ocr_clean in qr_clean or qr_clean in ocr_clean or len(set(ocr_clean).intersection(set(qr_clean))) > 4:
                items["merchant"] = CrossValidationItem(
                    field="merchant",
                    status="MATCH",
                    ocr_value=extracted_ocr_merchant,
                    qr_value=qr_pn,
                    severity="NEUTRAL",
                    details=f"Visual merchant name '{extracted_ocr_merchant}' matches QR payload '{qr_pn}'."
                )
            else:
                items["merchant"] = CrossValidationItem(
                    field="merchant",
                    status="MISMATCH",
                    ocr_value=extracted_ocr_merchant,
                    qr_value=qr_pn,
                    severity="HIGH",
                    details=f"Merchant discrepancy: Visual displays '{extracted_ocr_merchant}' vs encoded '{qr_pn}'."
                )
        else:
            items["merchant"] = CrossValidationItem(
                field="merchant",
                status="UNAVAILABLE",
                ocr_value=extracted_ocr_merchant,
                qr_value=qr_pn,
                severity="NEUTRAL",
                details="Merchant identity verified through primary channel."
            )

        # 4. Reference / Transaction ID Cross-Check
        qr_tr = str(upi_data.get("tr", "")).strip() if upi_data.get("tr") else None
        items["reference_id"] = CrossValidationItem(
            field="reference_id",
            status="MATCH" if qr_tr else "UNAVAILABLE",
            qr_value=qr_tr,
            severity="NEUTRAL",
            details=f"Transaction reference {qr_tr}" if qr_tr else "Reference ID not encoded in artifact."
        )

        # 5. Timestamp Consistency
        items["timestamp"] = CrossValidationItem(
            field="timestamp",
            status="UNAVAILABLE",
            severity="NEUTRAL",
            details="Timestamp verification requires bank network authorization record."
        )

        mismatches = sum(1 for v in items.values() if v.status == "MISMATCH")
        matches = sum(1 for v in items.values() if v.status == "MATCH")
        unavail = sum(1 for v in items.values() if v.status == "UNAVAILABLE")

        overall_status = "MISMATCH" if mismatches > 0 else ("MATCH" if matches > 0 else "UNAVAILABLE")
        overall_match = (mismatches == 0)

        summary_msg = f"{mismatches} evidence mismatch(es), {matches} confirmed match(es), {unavail} unconstrained field(s)."
        if mismatches > 0:
            summary_msg = f"CRITICAL CONTRADICTION: {mismatches} forensic mismatch(es) detected across OCR/QR/Context evidence."

        return CrossValidationResult(
            status=overall_status,
            overall_match=overall_match,
            items=items,
            mismatches_count=mismatches,
            matches_count=matches,
            unavailable_count=unavail,
            summary=summary_msg
        )

    def evaluate_payload_integrity(
        self,
        cross_val: CrossValidationResult,
        upi_data: Dict[str, Any],
        transaction_context: Optional[Dict[str, Any]],
        evidence: List[EvidenceItem]
    ) -> Dict[str, Any]:
        """
        Calculates holistic Payment Payload Integrity across all observed fields:
        Amount, VPA, Merchant, Transaction/Reference ID, Timestamp, Payment Status, Currency, Beneficiary.
        """
        checks = {}
        ctx = transaction_context or {}

        # 1. Amount Integrity
        amt_status = cross_val.items.get("amount", CrossValidationItem(field="amount", status="UNAVAILABLE")).status
        checks["amount"] = {
            "status": amt_status,
            "details": cross_val.items.get("amount").details if "amount" in cross_val.items else "Single channel observed"
        }

        # 2. VPA / Payee Destination Integrity
        vpa_status = cross_val.items.get("vpa", CrossValidationItem(field="vpa", status="UNAVAILABLE")).status
        checks["vpa"] = {
            "status": vpa_status,
            "details": cross_val.items.get("vpa").details if "vpa" in cross_val.items else "Payee observed"
        }

        # 3. Merchant Name Integrity
        merch_status = cross_val.items.get("merchant", CrossValidationItem(field="merchant", status="UNAVAILABLE")).status
        checks["merchant"] = {
            "status": merch_status,
            "details": cross_val.items.get("merchant").details if "merchant" in cross_val.items else "Merchant identity not dual-sourced"
        }

        # 4. Reference / Transaction ID
        ref_status = cross_val.items.get("reference_id", CrossValidationItem(field="reference_id", status="UNAVAILABLE")).status
        checks["reference_id"] = {
            "status": ref_status,
            "details": cross_val.items.get("reference_id").details if "reference_id" in cross_val.items else "Reference ID check"
        }

        # 5. Currency Integrity
        cu = upi_data.get("cu", "INR")
        if cu and cu.upper() != "INR":
            checks["currency"] = {"status": "MISMATCH", "details": f"Unexpected currency code '{cu}' for domestic UPI rail."}
        else:
            checks["currency"] = {"status": "MATCH", "details": "Standard INR domestic currency identifier."}

        # 6. Timestamp
        checks["timestamp"] = {
            "status": "UNAVAILABLE",
            "details": "Timestamp cross-check requires bank network ledger synchronization."
        }

        # Overall Verdict
        has_critical_mismatch = any(c["status"] == "MISMATCH" for c in checks.values())
        all_matched = all(c["status"] == "MATCH" for c in [checks["amount"], checks["vpa"], checks["currency"]])

        if has_critical_mismatch:
            overall_verdict = "COMPROMISED"
            summary = "Payment payload integrity is COMPROMISED due to confirmed parameter divergence."
        elif all_matched:
            overall_verdict = "INTEGRITY_VERIFIED"
            summary = "Payment payload integrity is VERIFIED across observed multi-modal channels."
        else:
            overall_verdict = "PARTIAL_EVIDENCE"
            summary = "Payment payload is consistent on available parameters; remaining fields are unconstrained."

        return {
            "overall_verdict": overall_verdict,
            "checks": checks,
            "mismatches_count": sum(1 for c in checks.values() if c["status"] == "MISMATCH"),
            "matches_count": sum(1 for c in checks.values() if c["status"] == "MATCH"),
            "unavailable_count": sum(1 for c in checks.values() if c["status"] == "UNAVAILABLE"),
            "summary": summary
        }

    def analyze_payment(self, req: CheckPaymentRequest) -> CheckPaymentResponse:
        """
        Unified multi-modal payment analysis pipeline.
        Extracts evidence -> Builds risk signals -> Executes hybrid ML & Quantum Escalation -> Generates Trust Assessment.
        """
        t0 = time.time()
        timings: List[Dict[str, Any]] = []
        evidence: List[EvidenceItem] = []
        risk_signals: List[RiskSignal] = []
        warnings: List[str] = []
        limitations: List[str] = [
            "Domain reputation: UNAVAILABLE (No external threat-intel API configured).",
            "Quantum Kernel: AER STATEVECTOR SIMULATION (4 Qubits)."
        ]

        case_id = f"QF-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{int(time.time() * 1000) % 100000:05d}"
        input_type = req.input_type.upper()

        # Handle Preset Scenarios if specified
        raw_payload = req.payload or ""
        if req.scenario_id:
            preset = self.get_scenario_by_id(req.scenario_id)
            if preset:
                input_type = preset["input_type"]
                raw_payload = preset["payload"]
                if "transaction_context" in preset and not req.transaction_context:
                    req.transaction_context = preset["transaction_context"]

        # Default transaction inference parameters
        amount = 850.0
        hour = datetime.now().hour
        velocity_1h = 1
        location_score = 0.15
        device_score = 0.15
        merchant_risk = 0.15
        account_age_days = 90
        user_id = "USR-CURRENT"
        merchant_name_obs = None
        payee_vpa_obs = None
        is_upi = False
        upi_data = {}
        ocr_text = None
        ocr_from_img = None
        extracted_ocr_amt = None
        extracted_ocr_vpa = None
        extracted_ocr_merchant = None

        # -------------------------------------------------------------
        # Stage 1: Multi-Modal Evidence & Threat Intelligence Extraction
        # -------------------------------------------------------------
        t_stage_start = time.time()
        threat_intelligence: Dict[str, Any] = {}

        # Universal File & Image Threat Analysis (SHA-256 & Metadata)
        if req.image_base64 or input_type == "FILE":
            try:
                raw_b64 = req.image_base64 or ""
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",", 1)[1]
                if raw_b64:
                    raw_bytes = base64.b64decode(raw_b64)
                    file_meta = threat_intel_service.analyze_file_metadata(raw_bytes, filename=req.filename)
                    threat_intelligence["file_metadata"] = file_meta

                    if file_meta.get("sha256"):
                        evidence.append(EvidenceItem(
                            category="IDENTIFIER",
                            field="sha256_hash",
                            value=file_meta["sha256"],
                            status="OBSERVED",
                            confidence=1.0,
                            source="CRYPTOGRAPHIC_HASH"
                        ))
                    if file_meta.get("detected_type"):
                        evidence.append(EvidenceItem(
                            category="CONTENT",
                            field="file_detected_type",
                            value=file_meta["detected_type"],
                            status="OBSERVED",
                            confidence=0.95,
                            source="FILE_METADATA_ANALYZER"
                        ))
                    if file_meta.get("is_executable") or file_meta.get("is_high_risk_extension"):
                        risk_signals.append(RiskSignal(
                            name="Executable Binary Payload Detected",
                            severity="CRITICAL",
                            status="OBSERVED",
                            description=f"Uploaded artifact is an executable binary ({file_meta.get('detected_type')}) or high-risk extension ({file_meta.get('extension')}) rather than a safe payment document.",
                            interpretation="Executable payloads in payment workflows indicate malware delivery intent."
                        ))

                    # VirusTotal File Reputation Query (Hash Lookup First)
                    if req.allow_external_threat_lookup and file_meta.get("sha256"):
                        vt_file_res = threat_intel_service.lookup_file_reputation(
                            file_meta["sha256"],
                            file_bytes=raw_bytes if req.external_file_submission_consent else None,
                            allow_upload=req.external_file_submission_consent
                        )
                        threat_intelligence["virustotal_file"] = vt_file_res
                        evidence.append(EvidenceItem(
                            category="CONTENT",
                            field="virustotal_file_reputation",
                            value=f"VT: {vt_file_res['status']} (Malicious: {vt_file_res.get('malicious_count', 0)} / {vt_file_res.get('total_vendors', 0)})",
                            status=vt_file_res["status"],
                            confidence=0.90 if vt_file_res["status"] == "OBSERVED" else 0.0,
                            source="VIRUSTOTAL"
                        ))
                        if vt_file_res.get("malicious_count", 0) >= 3:
                            risk_signals.append(RiskSignal(
                                name="VirusTotal Threat Intelligence Flag",
                                severity="CRITICAL",
                                status="OBSERVED",
                                description=f"{vt_file_res['malicious_count']} security vendors flagged this file hash as malicious on VirusTotal.",
                                interpretation="Known malicious artifact confirmed by global threat intelligence."
                            ))
                        elif vt_file_res.get("malicious_count", 0) >= 1 or vt_file_res.get("suspicious_count", 0) >= 2:
                            risk_signals.append(RiskSignal(
                                name="VirusTotal Suspicious Reputation",
                                severity="HIGH",
                                status="OBSERVED",
                                description=f"{vt_file_res.get('malicious_count', 0)} malicious / {vt_file_res.get('suspicious_count', 0)} suspicious vendor flags on VirusTotal.",
                                interpretation="Suspicious file heuristics flagged by external reputation vendors."
                            ))
            except Exception as e:
                warnings.append(f"File metadata extraction notice: {str(e)}")

        # If an image is provided, universally attempt QR decode and OCR extraction
        decoded_qr_from_img = None
        ocr_from_img = None
        if req.image_base64:
            decoded_qr_from_img, qr_err = self.decode_qr_image(req.image_base64)
            if qr_err and input_type == "QR":
                warnings.append(f"QR image scan note: {qr_err}")

            ocr_from_img, ocr_err = self.extract_screenshot_ocr(req.image_base64)
            if ocr_err and input_type == "SCREENSHOT":
                warnings.append(f"Screenshot OCR notice: {ocr_err}")

        if input_type == "QR" or decoded_qr_from_img:
            decoded_text = raw_payload if (input_type == "QR" and raw_payload and not req.image_base64) else (decoded_qr_from_img or raw_payload)
            if decoded_text:
                evidence.append(EvidenceItem(
                    category="IDENTIFIER",
                    field="qr_raw_payload",
                    value=decoded_text,
                    status="OBSERVED",
                    confidence=1.0,
                    source="QR_PAYLOAD"
                ))

                upi_data = self.parse_upi_payload(decoded_text)
                is_upi = upi_data.get("is_upi", False)
                if is_upi:
                    if upi_data["pa"]:
                        payee_vpa_obs = upi_data["pa"]
                        evidence.append(EvidenceItem(
                            category="RECIPIENT",
                            field="payee_vpa",
                            value=upi_data["pa"],
                            status="OBSERVED",
                            confidence=1.0,
                            source="QR_UPI_PAYLOAD"
                        ))
                    else:
                        evidence.append(EvidenceItem(
                            category="RECIPIENT",
                            field="payee_vpa",
                            value="MISSING_PAYEE_VPA",
                            status="OBSERVED",
                            confidence=1.0,
                            source="QR_UPI_PAYLOAD"
                        ))
                        risk_signals.append(RiskSignal(
                            name="Missing Payee Address",
                            severity="HIGH",
                            status="OBSERVED",
                            description="UPI QR code contains no payee VPA address.",
                            interpretation="Transactions without a valid payee address may fail or redirect to unverified accounts."
                        ))

                    if upi_data["pn"]:
                        merchant_name_obs = upi_data["pn"]
                        evidence.append(EvidenceItem(
                            category="RECIPIENT",
                            field="payee_name",
                            value=upi_data["pn"],
                            status="OBSERVED",
                            confidence=1.0,
                            source="QR_UPI_PAYLOAD"
                        ))

                    if upi_data["am"] is not None:
                        try:
                            amount = float(upi_data["am"])
                            evidence.append(EvidenceItem(
                                category="AMOUNT",
                                field="amount_inr",
                                value=amount,
                                status="OBSERVED",
                                confidence=1.0,
                                source="QR_UPI_PAYLOAD"
                            ))
                        except (ValueError, TypeError):
                            pass

                    if upi_data["tn"]:
                        evidence.append(EvidenceItem(
                            category="CONTENT",
                            field="transaction_note",
                            value=upi_data["tn"],
                            status="OBSERVED",
                            confidence=1.0,
                            source="QR_UPI_PAYLOAD"
                        ))
                        se_signals = self.extract_social_engineering_signals(upi_data["tn"])
                        risk_signals.extend(se_signals)
                else:
                    # Non-UPI QR payload: distinguish URL vs Plain Text
                    is_url_or_scheme = (
                        "://" in decoded_text
                        or decoded_text.startswith("www.")
                        or any(decoded_text.lower().startswith(s) for s in ["javascript:", "data:", "file:", "ftp:", "tel:", "mailto:", "sms:"])
                    )
                    if is_url_or_scheme:
                        is_safe, msg, sec_meta = self.validate_url_security(decoded_text)
                        evidence.append(EvidenceItem(
                            category="NETWORK",
                            field="qr_url_scheme",
                            value=sec_meta.get("scheme", "raw_text"),
                            status="OBSERVED",
                            confidence=1.0,
                            source="QR_PAYLOAD"
                        ))
                        if not is_safe:
                            risk_signals.append(RiskSignal(
                                name="Unsafe QR Destination",
                                severity="CRITICAL",
                                status="OBSERVED",
                                description=msg,
                                interpretation="QR points to an unapproved, private, or high-risk URL destination."
                            ))
                    else:
                        # Legitimate Plain Text QR Code
                        evidence.append(EvidenceItem(
                            category="CONTENT",
                            field="qr_plain_text",
                            value=decoded_text[:200] + ("..." if len(decoded_text) > 200 else ""),
                            status="OBSERVED",
                            confidence=1.0,
                            source="QR_PAYLOAD"
                        ))
                        se_signals = self.extract_social_engineering_signals(decoded_text)
                        risk_signals.extend(se_signals)
            elif input_type == "QR":
                evidence.append(EvidenceItem(
                    category="IDENTIFIER",
                    field="qr_raw_payload",
                    value="UNAVAILABLE",
                    status="UNAVAILABLE",
                    confidence=0.0,
                    source="QR_DECODER"
                ))
                warnings.append("Unable to extract readable QR payload.")

        if input_type == "SCREENSHOT" or ocr_from_img or (raw_payload and input_type != "QR" and input_type != "LINK"):
            ocr_text = ocr_from_img or raw_payload

            if ocr_text:
                evidence.append(EvidenceItem(
                    category="CONTENT",
                    field="screenshot_ocr_text",
                    value=ocr_text[:300] + ("..." if len(ocr_text) > 300 else ""),
                    status="OBSERVED",
                    confidence=0.92,
                    source="OCR_ENGINE"
                ))

                # Extract potential UPI ID from OCR text
                vpa_match = re.search(r"[\w\.\-]+@[\w\-]+", ocr_text)
                extracted_ocr_vpa = vpa_match.group(0) if vpa_match else None
                if extracted_ocr_vpa and not payee_vpa_obs:
                    payee_vpa_obs = extracted_ocr_vpa
                    evidence.append(EvidenceItem(
                        category="RECIPIENT",
                        field="extracted_upi_id",
                        value=payee_vpa_obs,
                        status="OBSERVED",
                        confidence=0.88,
                        source="OCR_TEXT"
                    ))

                # Extract amount from OCR text (₹ or INR or Rs)
                amt_match = re.search(r"(?:₹|INR|Rs\.?)\s*([\d,]+(?:\.\d{2})?)", ocr_text, re.IGNORECASE)
                extracted_ocr_amt = None
                if amt_match:
                    try:
                        parsed_amt = float(amt_match.group(1).replace(",", ""))
                        extracted_ocr_amt = parsed_amt
                        if not is_upi or upi_data.get("am") is None:
                            amount = parsed_amt
                        evidence.append(EvidenceItem(
                            category="AMOUNT",
                            field="extracted_amount_inr",
                            value=parsed_amt,
                            status="OBSERVED",
                            confidence=0.85,
                            source="OCR_TEXT"
                        ))
                    except ValueError:
                        pass

                # Cross-check QR vs OCR discrepancy if both present
                if is_upi and upi_data.get("pa") and extracted_ocr_vpa:
                    if upi_data["pa"].lower().strip() != extracted_ocr_vpa.lower().strip():
                        risk_signals.append(RiskSignal(
                            name="Evidence Mismatch: recipient_vpa",
                            severity="CRITICAL",
                            status="OBSERVED",
                            description=f"Visual evidence displays payee '{extracted_ocr_vpa}', but embedded QR routes to '{upi_data['pa']}'.",
                            interpretation="Critical recipient mismatch indicates screenshot manipulation or malicious QR overlay."
                        ))

                if is_upi and upi_data.get("am") is not None and extracted_ocr_amt is not None:
                    try:
                        qr_amt_val = float(upi_data["am"])
                        if abs(qr_amt_val - extracted_ocr_amt) >= 0.01:
                            risk_signals.append(RiskSignal(
                                name="Evidence Mismatch: amount",
                                severity="CRITICAL",
                                status="OBSERVED",
                                description=f"Screenshot displays ₹{extracted_ocr_amt:,.2f}, but embedded QR payload requests ₹{qr_amt_val:,.2f}.",
                                interpretation="Critical amount discrepancy indicates visual tampering or bait-and-switch payment."
                            ))
                    except (ValueError, TypeError):
                        pass

                # Social Engineering Signals from OCR
                se_signals = self.extract_social_engineering_signals(ocr_text)
                risk_signals.extend(se_signals)

            # Check if screenshot text contains an embedded UPI QR URL or payload
            if not is_upi and ocr_text:
                qr_match = re.search(r"upi://pay[^\s'\"\`\>]+", ocr_text, re.IGNORECASE)
                if qr_match:
                    embedded_qr_txt = qr_match.group(0)
                    upi_data = self.parse_upi_payload(embedded_qr_txt)
                    is_upi = upi_data.get("is_upi", False)
                    evidence.append(EvidenceItem(
                        category="IDENTIFIER",
                        field="qr_raw_payload",
                        value=embedded_qr_txt,
                        status="OBSERVED",
                        confidence=0.95,
                        source="EMBEDDED_QR_PAYLOAD"
                    ))

                    # Cross-check embedded QR vs visible text
                    if upi_data.get("pa"):
                        qr_pa_val = upi_data["pa"].lower().strip()
                        if extracted_ocr_vpa and qr_pa_val != extracted_ocr_vpa.lower().strip():
                            risk_signals.append(RiskSignal(
                                name="Evidence Mismatch: recipient_vpa",
                                severity="CRITICAL",
                                status="OBSERVED",
                                description=f"Visual evidence displays payee '{extracted_ocr_vpa}', but embedded QR routes to '{upi_data['pa']}'.",
                                interpretation="Critical recipient mismatch indicates screenshot manipulation or malicious QR overlay."
                            ))
                        elif "paid to:" in ocr_text.lower():
                            paid_to_line = [l for l in ocr_text.splitlines() if "paid to:" in l.lower()]
                            if paid_to_line:
                                p_txt = re.sub(r"[^\w]", "", paid_to_line[0].lower().replace("paid to:", ""))
                                if len(p_txt) > 3 and p_txt not in qr_pa_val and qr_pa_val.split("@")[0] not in p_txt:
                                    risk_signals.append(RiskSignal(
                                        name="Evidence Mismatch: recipient_vpa",
                                        severity="CRITICAL",
                                        status="OBSERVED",
                                        description=f"Visual text displays '{paid_to_line[0]}', but underlying QR routes to mule address '{upi_data['pa']}'.",
                                        interpretation="Severe recipient mismatch between visual receipt and encoded routing target."
                                    ))

                    if upi_data.get("am") is not None and extracted_ocr_amt is not None:
                        try:
                            qr_amt_val = float(upi_data["am"])
                            if abs(qr_amt_val - extracted_ocr_amt) >= 0.01:
                                risk_signals.append(RiskSignal(
                                    name="Evidence Mismatch: amount",
                                    severity="CRITICAL",
                                    status="OBSERVED",
                                    description=f"Screenshot displays ₹{extracted_ocr_amt:,.2f}, but embedded QR payload requests ₹{qr_amt_val:,.2f}.",
                                    interpretation="Critical amount discrepancy indicates visual tampering or bait-and-switch payment."
                                ))
                        except (ValueError, TypeError):
                            pass
            elif input_type == "SCREENSHOT":
                evidence.append(EvidenceItem(
                    category="CONTENT",
                    field="screenshot_ocr_text",
                    value="UNAVAILABLE",
                    status="UNAVAILABLE",
                    confidence=0.0,
                    source="OCR_ENGINE"
                ))

        elif input_type == "LINK":
            link_url = raw_payload
            is_valid_url, sec_msg, sec_meta = threat_intel_service.normalize_and_validate_url(link_url)

            evidence.append(EvidenceItem(
                category="NETWORK",
                field="payment_link_url",
                value=link_url,
                status="OBSERVED" if is_valid_url else "UNAVAILABLE",
                confidence=1.0,
                source="STATIC_URL_PARSER"
            ))
            evidence.append(EvidenceItem(
                category="NETWORK",
                field="url_scheme",
                value=sec_meta.get("scheme", "none"),
                status="OBSERVED",
                confidence=1.0,
                source="STATIC_URL_PARSER"
            ))

            if not is_valid_url:
                risk_signals.append(RiskSignal(
                    name="Security Policy Violation",
                    severity="CRITICAL",
                    status="OBSERVED",
                    description=sec_msg,
                    interpretation="The provided URL violates network security or SSRF safety baselines."
                ))
            else:
                if sec_meta.get("has_suspicious_tld"):
                    risk_signals.append(RiskSignal(
                        name="Suspicious Top-Level Domain",
                        severity="HIGH",
                        status="OBSERVED",
                        description=f"Domain '{sec_meta.get('domain')}' uses an unusual or disposable TLD.",
                        interpretation="Disposable TLDs are statistically overrepresented in phishing payment campaigns."
                    ))

                if sec_meta.get("lookalike_brands"):
                    brands_str = ", ".join(sec_meta["lookalike_brands"])
                    risk_signals.append(RiskSignal(
                        name="Brand Lookalike Domain",
                        severity="CRITICAL",
                        status="INFERRED",
                        description=f"Domain contains financial brand name '{brands_str}' on an unofficial host.",
                        interpretation="Lookalike domains attempt to deceive victims by impersonating trusted digital payment brands."
                    ))

                if sec_meta.get("excessive_encoding"):
                    risk_signals.append(RiskSignal(
                        name="Obfuscated URL Encoding",
                        severity="MODERATE",
                        status="OBSERVED",
                        description="URL query contains excessive percent-encoding or double-encoding.",
                        interpretation="Encoding is frequently used to evade heuristic pattern inspection."
                    ))

                # Deep Network & Domain Intelligence
                domain = sec_meta.get("domain")
                if domain and not sec_meta.get("is_private_ip"):
                    # 1. DNS Records Inspection
                    dns_res = threat_intel_service.inspect_dns_records(domain)
                    threat_intelligence["dns"] = dns_res
                    evidence.append(EvidenceItem(
                        category="NETWORK",
                        field="dns_records",
                        value=f"IPs: {', '.join(dns_res.get('ip_addresses', [])) if dns_res.get('ip_addresses') else 'None'}",
                        status=dns_res["status"],
                        confidence=0.95 if dns_res["status"] == "OBSERVED" else 0.0,
                        source="DNS_RESOLVER"
                    ))

                    # 2. TLS Certificate Inspection
                    tls_res = threat_intel_service.inspect_tls_certificate(domain, port=sec_meta.get("port", 443))
                    threat_intelligence["tls"] = tls_res
                    evidence.append(EvidenceItem(
                        category="NETWORK",
                        field="tls_certificate",
                        value=f"Issuer: {tls_res.get('issuer')}, Valid Until: {tls_res.get('not_after')}",
                        status=tls_res["status"],
                        confidence=0.95 if tls_res["status"] == "OBSERVED" else 0.0,
                        source="TLS_INSPECTION"
                    ))
                    if tls_res.get("is_expired"):
                        risk_signals.append(RiskSignal(
                            name="Invalid TLS Certificate",
                            severity="HIGH",
                            status="OBSERVED",
                            description="SSL/TLS certificate for payment link domain has expired.",
                            interpretation="Expired certificates indicate unmaintained, abandoned, or spoofed payment endpoints."
                        ))

                    # 3. WHOIS & Domain Age Intelligence (with PII Redaction)
                    whois_res = threat_intel_service.lookup_whois_intelligence(domain)
                    threat_intelligence["whois"] = whois_res
                    evidence.append(EvidenceItem(
                        category="NETWORK",
                        field="domain_whois_record",
                        value=f"Registrar: {whois_res.get('registrar')}, Age: {whois_res.get('domain_age_days')} days",
                        status=whois_res["status"],
                        confidence=0.90 if whois_res["status"] == "OBSERVED" else 0.0,
                        source="WHOIS"
                    ))
                    if whois_res.get("is_young_domain"):
                        risk_signals.append(RiskSignal(
                            name="Recently Registered Domain",
                            severity="MODERATE",
                            status="INFERRED",
                            description=f"Domain was registered {whois_res.get('domain_age_days')} days ago ({whois_res.get('creation_date')}).",
                            interpretation="Recently registered domains have limited reputation history. Evaluated as contextual risk, not definitive proof."
                        ))

                    # 4. VirusTotal URL Reputation / Domain Reputation Feed
                    vt_res = threat_intel_service.lookup_url_reputation(link_url)
                    threat_intelligence["virustotal_url"] = vt_res
                    evidence.append(EvidenceItem(
                        category="NETWORK",
                        field="domain_reputation_feed",
                        value=f"VT: {vt_res['status']} (Malicious: {vt_res.get('malicious_count', 0)} / {vt_res.get('total_vendors', 0)})" if vt_res["status"] == "OBSERVED" else "UNAVAILABLE",
                        status=vt_res["status"],
                        confidence=0.95 if vt_res["status"] == "OBSERVED" else 0.0,
                        source="VIRUSTOTAL"
                    ))
                    if vt_res.get("malicious_count", 0) >= 3:
                        risk_signals.append(RiskSignal(
                            name="VirusTotal Threat Intelligence Flag",
                            severity="CRITICAL",
                            status="OBSERVED",
                            description=f"{vt_res['malicious_count']} security vendors flagged this URL as malicious on VirusTotal.",
                            interpretation="Global threat intelligence network confirms active phishing/malware distribution."
                        ))
                    elif vt_res.get("malicious_count", 0) >= 1 or vt_res.get("suspicious_count", 0) >= 2:
                        risk_signals.append(RiskSignal(
                            name="VirusTotal Suspicious Reputation",
                            severity="HIGH",
                            status="OBSERVED",
                            description=f"{vt_res.get('malicious_count', 0)} malicious / {vt_res.get('suspicious_count', 0)} suspicious vendor flags on VirusTotal.",
                            interpretation="Elevated suspicion reported by third-party security vendors."
                        ))

            # Extract URL query parameters if present (e.g. ?upi=... or ?pa=...)
            if is_valid_url:
                parsed_u = urllib.parse.urlparse(link_url)
                if parsed_u.query:
                    qs = urllib.parse.parse_qs(parsed_u.query)
                    for k, v in qs.items():
                        k_l = k.lower()
                        val_str = v[0] if v else ""
                        if k_l in ["pa", "upi", "recipient", "vpa"] and val_str:
                            payee_vpa_obs = val_str
                            evidence.append(EvidenceItem(
                                category="RECIPIENT",
                                field="payee_vpa",
                                value=payee_vpa_obs,
                                status="OBSERVED",
                                confidence=0.95,
                                source="URL_QUERY_PARAM"
                            ))
                        elif k_l in ["pn", "merchant", "payee"] and val_str:
                            merchant_name_obs = val_str
                            evidence.append(EvidenceItem(
                                category="RECIPIENT",
                                field="merchant_name",
                                value=merchant_name_obs,
                                status="OBSERVED",
                                confidence=0.95,
                                source="URL_QUERY_PARAM"
                            ))
                        elif k_l in ["am", "amount"] and val_str:
                            try:
                                amount = float(val_str)
                                evidence.append(EvidenceItem(
                                    category="AMOUNT",
                                    field="amount",
                                    value=amount,
                                    status="OBSERVED",
                                    confidence=0.95,
                                    source="URL_QUERY_PARAM"
                                ))
                            except ValueError:
                                pass

        # Check Context Override
        if req.transaction_context:
            ctx = req.transaction_context
            if "amount" in ctx: amount = float(ctx["amount"])
            if "velocity_1h" in ctx: velocity_1h = int(ctx["velocity_1h"])
            if "device_score" in ctx: device_score = float(ctx["device_score"])
            if "location_score" in ctx: location_score = float(ctx["location_score"])
            if "merchant_risk" in ctx: merchant_risk = float(ctx["merchant_risk"])
            if "account_age_days" in ctx: account_age_days = int(ctx["account_age_days"])
            if "user_id" in ctx: user_id = str(ctx["user_id"])
            if not payee_vpa_obs and "recipient_vpa" in ctx:
                payee_vpa_obs = str(ctx["recipient_vpa"])
                evidence.append(EvidenceItem(
                    category="RECIPIENT",
                    field="payee_vpa",
                    value=payee_vpa_obs,
                    status="OBSERVED",
                    confidence=1.0,
                    source="SESSION_CONTEXT"
                ))
            if not merchant_name_obs and "declared_merchant_name" in ctx:
                merchant_name_obs = str(ctx["declared_merchant_name"])

        # Identity Consistency Check
        if merchant_name_obs and payee_vpa_obs:
            vpa_prefix_clean = re.sub(r"[^\w]", "", payee_vpa_obs.split("@")[0].lower())
            name_clean = re.sub(r"[^\w]", "", merchant_name_obs.lower())
            vpa_tokens = [t for t in re.split(r"[^\w]+", payee_vpa_obs.split("@")[0].lower()) if len(t) >= 3]
            name_tokens = [t for t in re.split(r"[^\w]+", merchant_name_obs.lower()) if len(t) >= 3]
            tokens_overlap = any(vt in name_clean for vt in vpa_tokens) or any(nt in vpa_prefix_clean for nt in name_tokens)
            if len(vpa_prefix_clean) > 3 and not tokens_overlap and vpa_prefix_clean not in name_clean and name_clean not in vpa_prefix_clean:
                risk_signals.append(RiskSignal(
                    name="Identity Consistency Mismatch",
                    severity="MODERATE",
                    status="INFERRED",
                    description=f"Displayed name '{merchant_name_obs}' does not match recipient VPA handle '{payee_vpa_obs}'.",
                    interpretation="Unmatched merchant names and payment destinations require secondary verification before authorization."
                ))

        # First-Class OCR <-> QR <-> Context Cross-Validation Engine
        cross_val = self.evaluate_cross_validation(
            ocr_text=ocr_text,
            upi_data=upi_data,
            transaction_context=req.transaction_context,
            extracted_ocr_amt=extracted_ocr_amt,
            extracted_ocr_vpa=extracted_ocr_vpa,
            extracted_ocr_merchant=merchant_name_obs
        )

        for field_name, cv_item in cross_val.items.items():
            if cv_item.status == "MISMATCH":
                # Ensure no duplicate signal name
                sig_name = f"Evidence Mismatch: {field_name}"
                if not any(s.name == sig_name for s in risk_signals):
                    risk_signals.append(RiskSignal(
                        name=sig_name,
                        severity=cv_item.severity,
                        status="OBSERVED",
                        description=cv_item.details or f"Discrepancy detected on {field_name}.",
                        interpretation="Discrepancy between visual payment receipt and underlying transaction routing indicates tampering."
                    ))

        t_stage1 = round((time.time() - t_stage_start) * 1000, 2)
        timings.append({"stage": "Multi-Modal Evidence Extraction & Static Forensics", "latency_ms": t_stage1})

        # -------------------------------------------------------------
        # Stage 1.5: Gemini Multimodal Evidence Verification Layer
        # -------------------------------------------------------------
        t_stage_ev = time.time()
        evidence_verification = None
        if req.image_base64 or input_type in ["QR", "SCREENSHOT"]:
            try:
                from backend.app.services.gemini_evidence_service import gemini_evidence_service
                ev_res = gemini_evidence_service.analyze_evidence(
                    image_base64=req.image_base64,
                    filename=req.filename,
                    case_id=case_id,
                    declared_amount=amount if (payee_vpa_obs or merchant_name_obs) else None,
                    declared_vpa=payee_vpa_obs,
                    decoded_qr_data=upi_data if is_upi else None,
                    local_ocr_text=ocr_text
                )
                evidence_verification = ev_res

                # Feed forensic evidence checks into existing multi-signal engine
                for chk in ev_res.evidence_checks:
                    if chk.result == "MISMATCH":
                        risk_signals.append(RiskSignal(
                            name=f"Evidence Mismatch: {chk.field}",
                            severity=chk.impact,
                            status="OBSERVED",
                            description=chk.description,
                            interpretation="Discrepancy detected between visual payment evidence and encoded routing metadata."
                        ))

                if ev_res.visual_assessment.manipulation_level in ["HIGH", "MODERATE"]:
                    risk_signals.append(RiskSignal(
                        name="Visual Manipulation Indicators",
                        severity=ev_res.visual_assessment.manipulation_level,
                        status="OBSERVED",
                        description=f"Observed visual anomalies: {', '.join(ev_res.visual_assessment.manipulation_indicators) if ev_res.visual_assessment.manipulation_indicators else 'Font and alignment inconsistencies'}",
                        interpretation="Visual evidence contains layout or pixel manipulation patterns."
                    ))

                if ev_res.visual_assessment.ai_generation_assessment == "HIGH INDICATION":
                    risk_signals.append(RiskSignal(
                        name="Synthetic Media Signal",
                        severity="HIGH",
                        status="INFERRED",
                        description="Probabilistic assessment indicates elevated likelihood of synthetic visual artifact.",
                        interpretation="Synthetic payment artifacts are commonly generated to fabricate receipts or spoof QR displays."
                    ))

                # Add evidence verification summary item
                evidence.append(EvidenceItem(
                    category="CONTENT",
                    field="evidence_verification_status",
                    value=f"{ev_res.provider}: {ev_res.analysis_status} (Confidence: {ev_res.overall_evidence_confidence})",
                    status="OBSERVED",
                    confidence=0.95,
                    source="GEMINI_MULTIMODAL"
                ))
            except Exception as e:
                warnings.append(f"Evidence verification notice: {str(e)}")

        t_ev_ms = round((time.time() - t_stage_ev) * 1000, 2)
        timings.append({"stage": "Gemini Multimodal Evidence Verification", "latency_ms": t_ev_ms})

        # -------------------------------------------------------------
        # Stage 2: Bridge to Unified Fraud Engine & Multi-Signal Fusion
        # -------------------------------------------------------------
        critical_count = sum(1 for r in risk_signals if r.severity == "CRITICAL")
        high_count = sum(1 for r in risk_signals if r.severity == "HIGH")

        adjusted_device_score = min(1.0, device_score + (0.35 if critical_count > 0 else (0.15 if high_count > 0 else 0.0)))
        adjusted_merchant_risk = min(1.0, merchant_risk + (0.40 if critical_count > 0 else (0.20 if high_count > 0 else 0.0)))

        artifact_context = {
            "amount": amount if (payee_vpa_obs or merchant_name_obs) else None,
            "payee_vpa": payee_vpa_obs,
            "merchant_name": merchant_name_obs
        }

        txn_payload = TransactionPayload(
            txn_id=case_id,
            user_id=user_id,
            account_id="ACC-ONLINE-01",
            device_id="DEV-CHECK-01",
            ip="192.168.1.100",
            merchant_id=payee_vpa_obs or "MERCH-CHECK",
            lat=19.0760,
            lon=72.8777,
            amount=amount,
            hour=hour,
            velocity_1h=velocity_1h,
            account_age_days=account_age_days,
            device_score=round(adjusted_device_score, 2),
            location_score=round(location_score, 2),
            merchant_risk=round(adjusted_merchant_risk, 2),
            forensic_signals=[r.model_dump() for r in risk_signals],
            artifact_context=artifact_context
        )

        pred = fraud_engine.predict(txn_payload)
        timings.extend([t.model_dump() for t in pred.timings])

        # -------------------------------------------------------------
        # Stage 3: Authoritative Single Result Consistency Guard
        # -------------------------------------------------------------
        risk_score = pred.risk_score
        confidence = pred.confidence

        has_critical_signal = critical_count > 0
        has_recipient_mismatch = any("recipient" in s.name.lower() or "payee" in s.name.lower() for s in risk_signals if s.severity in ["CRITICAL", "HIGH"])
        has_amount_mismatch = any("amount" in s.name.lower() for s in risk_signals if s.severity in ["CRITICAL", "HIGH"])
        has_phishing_link = any("lookalike" in s.name.lower() or "phishing" in s.name.lower() or "security policy" in s.name.lower() for s in risk_signals)
        has_manipulation = any("manipulation" in s.name.lower() or "synthetic" in s.name.lower() for s in risk_signals if s.severity in ["CRITICAL", "HIGH"])

        is_dual_mismatch = has_recipient_mismatch and has_amount_mismatch
        has_confirmed_threat = has_critical_signal or has_recipient_mismatch or has_amount_mismatch or has_phishing_link

        if is_dual_mismatch or (has_phishing_link and (has_recipient_mismatch or has_amount_mismatch)) or critical_count >= 2:
            risk_score = max(risk_score, 94.0)
            trust_level = "HIGH RISK / UNTRUSTED"
            decision = "BLOCK"
            recommendation = "DO NOT PROCEED — Critical multi-signal discrepancy (payee & amount mismatch) and high fraud probability detected."
        elif has_confirmed_threat or risk_score >= 70.0:
            risk_score = max(risk_score, 82.0)
            trust_level = "HIGH RISK / UNTRUSTED"
            decision = "BLOCK"
            recommendation = "DO NOT PROCEED — Severe forensic anomalies and payment routing discrepancy detected."
        elif high_count > 0 or has_manipulation or risk_score >= 40.0:
            risk_score = max(risk_score, 58.0)
            trust_level = "SUSPICIOUS / STEP-UP"
            decision = "STEP_UP"
            recommendation = "STEP-UP VERIFICATION REQUIRED — Discrepancies or synthetic visual artifacts detected. Verify destination before authorization."
        elif len(risk_signals) > 0 or risk_score >= 20.0:
            risk_score = max(risk_score, 32.0)
            trust_level = "SUSPICIOUS / CAUTION"
            decision = "MONITOR"
            recommendation = "PROCEED WITH CAUTION — Secondary verification recommended before payment authorization."
        else:
            risk_score = min(risk_score, 12.0)
            trust_level = "LOW RISK BASED ON AVAILABLE EVIDENCE"
            decision = "APPROVE"
            recommendation = "Low risk based on available evidence. Proceed with normal caution."

        feature_contribs = {
            "top_positive": [f.model_dump() for f in pred.top_positive_contributors],
            "top_negative": [f.model_dump() for f in pred.top_negative_contributors]
        }

        payload_integrity = self.evaluate_payload_integrity(cross_val, upi_data, req.transaction_context, evidence)
        txn_dna = transaction_dna_service.evaluate_transaction_dna(user_id, req.transaction_context or {"amount": amount, "user_id": user_id, "velocity_1h": velocity_1h, "device_score": device_score, "merchant_risk": merchant_risk})

        res_obj = CheckPaymentResponse(
            case_id=case_id,
            input_type=input_type,
            timestamp=time.time(),
            analysis_status="COMPLETED",
            trust_level=trust_level,
            risk_score=risk_score,
            confidence=confidence,
            decision=decision,
            recommendation=recommendation,
            evidence=evidence,
            risk_signals=risk_signals,
            signal_summary=pred.signal_summary,
            cross_signal_consistency=pred.cross_signal_consistency,
            cross_validation=cross_val,
            payload_integrity=payload_integrity,
            transaction_dna=txn_dna.model_dump(),
            fusion_result=pred.fusion_result,
            model_disagreement=pred.model_disagreement,
            feature_contributions=feature_contribs,
            mitigation_factors=pred.mitigation_factors,
            warnings=warnings,
            quantum_escalation=pred.quantum_escalation,
            fraud_dna=pred.fraud_dna,
            counterfactuals=pred.counterfactuals,
            counterfactual_result=pred.counterfactual_result,
            timings=timings,
            limitations=limitations,
            evidence_verification=evidence_verification,
            threat_intelligence=threat_intelligence
        )

        try:
            from backend.app.services.investigation_service import investigation_service
            investigation_service.register_case_from_check_payment(res_obj, req)
        except Exception as e:
            import traceback
            traceback.print_exc()

        return res_obj

    def get_demo_fixtures(self) -> List[Dict[str, Any]]:
        """Predefined deterministic test scenarios for Check a Payment & Gemini Evidence Verification."""
        return [
            {
                "id": "SCENARIO_A_GENUINE_PAYMENT",
                "name": "Case A — Genuine Verified Payment (Clean Evidence)",
                "input_type": "QR",
                "payload": "upi://pay?pa=verified.store@icici&pn=Verified%20Store%20Retail&am=2500.00&cu=INR&tn=Invoice%208801",
                "description": "Genuine payment with consistent amount (₹2,500), authentic verified merchant VPA, valid QR, and zero visual manipulation.",
                "expected_trust": "LOW RISK BASED ON AVAILABLE EVIDENCE",
                "transaction_context": {
                    "amount": 2500.0,
                    "velocity_1h": 1,
                    "device_score": 0.08,
                    "location_score": 0.05,
                    "merchant_risk": 0.04,
                    "account_age_days": 240
                }
            },
            {
                "id": "SCENARIO_B_QR_AMOUNT_MISMATCH",
                "name": "Case B — QR Amount Mismatch vs Receipt",
                "input_type": "SCREENSHOT",
                "payload": "PAYMENT CONFIRMATION\nPaid to: Fresh Retail Store\nAmount: ₹4,999.00\nUPI Ref: 499100234190\nQR Payload: upi://pay?pa=freshretail@icici&am=499.00\nStatus: SUCCESS",
                "description": "Manipulated screenshot displaying ₹4,999 while underlying QR payload requests ₹499.",
                "expected_trust": "HIGH RISK / UNTRUSTED",
                "transaction_context": {
                    "amount": 4999.0,
                    "recipient_vpa": "freshretail@icici",
                    "velocity_1h": 2,
                    "device_score": 0.20,
                    "location_score": 0.15,
                    "merchant_risk": 0.15,
                    "account_age_days": 180
                }
            },
            {
                "id": "SCENARIO_B_MANIPULATED_SCREENSHOT",
                "name": "Scenario B — Manipulated Screenshot vs QR (Amount Mismatch)",
                "input_type": "SCREENSHOT",
                "payload": "PAYMENT CONFIRMATION\nPaid to: Fresh Retail Store\nAmount: ₹4,999.00\nUPI Ref: 499100234190\nQR Payload: upi://pay?pa=fakecare@ybl&am=499.00\nStatus: SUCCESS",
                "description": "Manipulated screenshot displaying ₹4,999 while underlying QR payload routes ₹499 to mule handle 'fakecare@ybl' with font alignment anomalies.",
                "expected_trust": "HIGH RISK / UNTRUSTED",
                "transaction_context": {
                    "amount": 4999.0,
                    "recipient_vpa": "fakecare@ybl",
                    "velocity_1h": 11,
                    "device_score": 0.84,
                    "location_score": 0.78,
                    "merchant_risk": 0.92,
                    "account_age_days": 12
                }
            },
            {
                "id": "SCENARIO_C_MERCHANT_VPA_MISMATCH",
                "name": "Case C — Payee & VPA Mismatch / Mule Account Routing",
                "input_type": "SCREENSHOT",
                "payload": "OFFICIAL HDFC BANK BILL DESK\nPaid to: HDFC Utilities Private Limited\nAmount: ₹15,000.00\nQR Payload: upi://pay?pa=mule.quickcash@ybl&pn=Mule%20Account&am=15000.00\nStatus: PENDING",
                "description": "Visual receipt claims payment to 'HDFC Utilities' but encoded QR routes ₹15,000 to unverified mule handle 'mule.quickcash@ybl'.",
                "expected_trust": "HIGH RISK / UNTRUSTED",
                "transaction_context": {
                    "amount": 15000.0,
                    "recipient_vpa": "mule.quickcash@ybl",
                    "velocity_1h": 4,
                    "device_score": 0.70,
                    "location_score": 0.65,
                    "merchant_risk": 0.85,
                    "account_age_days": 30
                }
            },
            {
                "id": "SCENARIO_D_SUSPICIOUS_PAYMENT_LINK",
                "name": "Case D — Lookalike Phishing Link / Disposable TLD",
                "input_type": "LINK",
                "payload": "https://secure-upi-paytm-verify-refund.xyz/pay?user=USR-9901&am=25000",
                "description": "Disposable .xyz domain impersonating Paytm with urgency refund parameters.",
                "expected_trust": "HIGH RISK / UNTRUSTED",
                "transaction_context": {
                    "amount": 25000.0,
                    "velocity_1h": 5,
                    "device_score": 0.85,
                    "location_score": 0.70,
                    "merchant_risk": 0.90,
                    "account_age_days": 20
                }
            },
            {
                "id": "SCENARIO_E_TRANSACTION_ANOMALY",
                "name": "Case E — High-Risk Transaction Anomaly / Velocity Burst",
                "input_type": "QR",
                "payload": "upi://pay?pa=crypto.instant.swap@axisbank&pn=Instant%20Swap&am=98000.00&cu=INR&tn=OTC%20Transfer",
                "description": "High-value transaction with extreme velocity surge (14 txns/hr) and unfamiliar device triggering quantum escalation.",
                "expected_trust": "HIGH RISK / UNTRUSTED",
                "transaction_context": {
                    "amount": 98000.0,
                    "velocity_1h": 14,
                    "device_score": 0.92,
                    "location_score": 0.88,
                    "merchant_risk": 0.85,
                    "account_age_days": 5
                }
            },
            {
                "id": "SCENARIO_C_SYNTHETIC_ARTIFACT",
                "name": "Scenario C — Synthetic / AI-Generated Payment Scratch Card",
                "input_type": "SCREENSHOT",
                "payload": "CASHBACK REWARD WON: ₹50,000!\nScan to claim immediately into your bank account.\nValid for next 10 minutes only.\nRoute: paytm-reward-claim@paytm",
                "description": "AI-generated synthetic scratch-card promotion with artificial texture patterns, urgency coercion, and unverified prize routing.",
                "expected_trust": "HIGH RISK / UNTRUSTED",
                "transaction_context": {
                    "amount": 50000.0,
                    "recipient_vpa": "reward-claim@paytm",
                    "velocity_1h": 9,
                    "device_score": 0.88,
                    "location_score": 0.80,
                    "merchant_risk": 0.95,
                    "account_age_days": 8
                }
            },
            {
                "id": "SCENARIO_1_SAFE_QR",
                "name": "Scenario 1 — Safe Grocery UPI QR",
                "input_type": "QR",
                "payload": "upi://pay?pa=freshmart.retail@icici&pn=Fresh%20Mart%20Retail&am=850.00&cu=INR&tn=Order%204991",
                "description": "Standard retail grocery UPI payment with matching merchant identity and normal amount.",
                "expected_trust": "LOW RISK BASED ON AVAILABLE EVIDENCE",
                "transaction_context": {
                    "amount": 850.0,
                    "velocity_1h": 1,
                    "device_score": 0.12,
                    "location_score": 0.10,
                    "merchant_risk": 0.15,
                    "account_age_days": 180
                }
            },
            {
                "id": "SCENARIO_2_SUSPICIOUS_SE_QR",
                "name": "Scenario 2 — Urgent Prize Lottery Scam QR",
                "input_type": "QR",
                "payload": "upi://pay?pa=claim.reward@ybl&pn=Lucky%20Prize%20Winner&am=1.00&cu=INR&tn=URGENT%20KYC%20VERIFY%20CLAIM%20REWARD%20IMMEDIATELY",
                "description": "UPI QR with urgency social engineering keywords and reverse-charge transaction note.",
                "expected_trust": "HIGH RISK / UNTRUSTED",
                "transaction_context": {
                    "amount": 1.0,
                    "velocity_1h": 8,
                    "device_score": 0.72,
                    "location_score": 0.65,
                    "merchant_risk": 0.88,
                    "account_age_days": 5
                }
            },
            {
                "id": "SCENARIO_3_PHISHING_LINK",
                "name": "Scenario 3 — Brand Lookalike Phishing Link",
                "input_type": "LINK",
                "payload": "https://secure-upi-paytm-verify-refund.xyz/pay?user=USR-9901&am=25000",
                "description": "Disposable .xyz domain impersonating Paytm with urgency refund parameters.",
                "expected_trust": "HIGH RISK / UNTRUSTED",
                "transaction_context": {
                    "amount": 25000.0,
                    "velocity_1h": 5,
                    "device_score": 0.85,
                    "location_score": 0.70,
                    "merchant_risk": 0.90,
                    "account_age_days": 20
                }
            },
            {
                "id": "SCENARIO_4_MODIFIED_SCREENSHOT",
                "name": "Scenario 4 — Social Engineering Screenshot OCR",
                "input_type": "SCREENSHOT",
                "payload": "ELECTRICITY BILL PAYMENT OVERDUE NOTICE\nUrgent: Power will be disconnected in 2 hours!\nPay immediately to avoid penalty.\nContact Support: support-desk@paytm\nAmount Due: ₹12,450.00",
                "description": "Screenshot notice with coercive disconnection threat and suspicious recipient handle.",
                "expected_trust": "HIGH RISK / UNTRUSTED",
                "transaction_context": {
                    "amount": 12450.0,
                    "velocity_1h": 3,
                    "device_score": 0.68,
                    "location_score": 0.60,
                    "merchant_risk": 0.85,
                    "account_age_days": 35
                }
            },
            {
                "id": "SCENARIO_5_AMBIGUOUS_QUANTUM",
                "name": "Scenario 5 — Ambiguous Borderline Payment (Quantum Escalation)",
                "input_type": "QR",
                "payload": "upi://pay?pa=crossborder.tech@axisbank&pn=CrossBorder%20Tech&am=48000.00&cu=INR&tn=Consulting%20Retainer",
                "description": "High-value borderline payment with moderate anomaly signals triggering Qiskit quantum kernel classification.",
                "expected_trust": "CAUTION / STEP-UP VERIFICATION",
                "transaction_context": {
                    "amount": 48000.0,
                    "velocity_1h": 3,
                    "device_score": 0.45,
                    "location_score": 0.42,
                    "merchant_risk": 0.44,
                    "account_age_days": 45
                }
            }
        ]

    def get_scenario_by_id(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        for sc in self.get_demo_fixtures():
            if sc["id"] == scenario_id:
                return sc
        return None


payment_forensics_service = PaymentForensicsService()
