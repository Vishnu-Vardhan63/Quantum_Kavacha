import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.transaction import TransactionPayload
from backend.app.services.fraud_engine import fraud_engine

client = TestClient(app)

# ---------------------------------------------------------------------------
# Unit / Logic Tests: Alert Trigger Conditions, Deduplication & Mute Handling
# ---------------------------------------------------------------------------

def is_high_risk_alert_verdict(result_dict: dict, is_analyzing: bool = False) -> bool:
    """
    Python mirror of the exact frontend detection policy logic implemented in
    DetectionCenterWorkspace.jsx (`isHighRiskVerdict`).
    """
    if not result_dict or is_analyzing:
        return False
    decision = str(result_dict.get("decision", "")).upper()
    score = float(result_dict.get("risk_score", 0.0))
    trust = str(result_dict.get("trust_level", "")).upper()
    risk_level = str(result_dict.get("risk_level", "")).upper()

    return (
        decision == "BLOCK" or
        score >= 70.0 or
        "HIGH RISK" in trust or
        "HIGH RISK" in risk_level
    )


class AudioAlertControllerMock:
    """
    Simulates browser Web Audio player state, user controls (mute/unmute, enable/disable),
    deduplication across renders, and browser audio failure handling.
    """
    def __init__(self, browser_audio_supported: bool = True, autoplay_blocked: bool = False):
        self.audio_enabled = True
        self.is_muted = False
        self.audio_status = "IDLE"
        self.audio_count = 0
        self.last_alert_case_id = None
        self.browser_audio_supported = browser_audio_supported
        self.autoplay_blocked = autoplay_blocked

    def receive_detection_result(self, result: dict, is_analyzing: bool = False):
        if not result or is_analyzing:
            return

        case_id = result.get("case_id") or f"{result.get('timestamp')}-{result.get('risk_score')}"
        should_alert = is_high_risk_alert_verdict(result, is_analyzing)

        # Deduplication check: only fire if this is a distinct result / case that hasn't sounded
        if should_alert and self.last_alert_case_id != case_id:
            self.last_alert_case_id = case_id

            if not self.audio_enabled:
                self.audio_status = "DISABLED"
                return

            if self.is_muted:
                self.audio_status = "MUTED"
                return

            if not self.browser_audio_supported or self.autoplay_blocked:
                self.audio_status = "RESTRICTED"
                return

            # Successful tone playback
            self.audio_status = "IDLE"
            self.audio_count += 1

    def replay_alert(self, result: dict):
        if not result or not is_high_risk_alert_verdict(result):
            return
        if self.is_muted:
            self.is_muted = False

        if not self.browser_audio_supported or self.autoplay_blocked:
            self.audio_status = "RESTRICTED"
            return

        self.audio_status = "IDLE"
        self.audio_count += 1


def test_benign_results_do_not_trigger_sound():
    """Verify clean/benign payment verdicts NEVER trigger the audible alert."""
    controller = AudioAlertControllerMock()

    benign_result = {
        "case_id": "CASE-BENIGN-001",
        "decision": "APPROVE",
        "risk_score": 12.0,
        "trust_level": "LOW RISK BASED ON AVAILABLE EVIDENCE",
        "risk_level": "NORMAL"
    }

    assert is_high_risk_alert_verdict(benign_result) is False
    controller.receive_detection_result(benign_result)
    assert controller.audio_count == 0
    assert controller.audio_status == "IDLE"


def test_high_risk_results_trigger_sound_exactly_once():
    """Verify high-risk or BLOCK verdict triggers the sound exactly once, and rerenders do not repeat."""
    controller = AudioAlertControllerMock()

    high_risk_result = {
        "case_id": "CASE-MALICIOUS-001",
        "decision": "BLOCK",
        "risk_score": 94.0,
        "trust_level": "HIGH RISK / UNTRUSTED",
        "risk_level": "HIGH RISK"
    }

    assert is_high_risk_alert_verdict(high_risk_result) is True

    # 1. First trigger
    controller.receive_detection_result(high_risk_result)
    assert controller.audio_count == 1

    # 2. Rerenders / state updates for the same case must NOT re-trigger audio
    controller.receive_detection_result(high_risk_result)
    controller.receive_detection_result(high_risk_result)
    assert controller.audio_count == 1

    # 3. A distinct new high-risk investigation case DOES trigger a new sound
    new_high_risk_result = {
        "case_id": "CASE-MALICIOUS-002",
        "decision": "BLOCK",
        "risk_score": 85.0,
        "trust_level": "HIGH RISK / UNTRUSTED",
        "risk_level": "HIGH RISK"
    }
    controller.receive_detection_result(new_high_risk_result)
    assert controller.audio_count == 2


def test_mute_and_enable_controls():
    """Verify mute control silences playback while maintaining visual warning state."""
    controller = AudioAlertControllerMock()
    controller.is_muted = True

    high_risk_result = {
        "case_id": "CASE-MUTED-001",
        "decision": "BLOCK",
        "risk_score": 88.0,
        "trust_level": "HIGH RISK / UNTRUSTED"
    }

    controller.receive_detection_result(high_risk_result)
    # Count remains 0 because audio is muted
    assert controller.audio_count == 0
    assert controller.audio_status == "MUTED"
    # Visual verdict is still HIGH RISK
    assert is_high_risk_alert_verdict(high_risk_result) is True


def test_replay_alert_control():
    """Verify user can manually replay warning tone for active high-risk finding."""
    controller = AudioAlertControllerMock()

    high_risk_result = {
        "case_id": "CASE-REPLAY-001",
        "decision": "BLOCK",
        "risk_score": 92.0
    }

    controller.receive_detection_result(high_risk_result)
    assert controller.audio_count == 1

    # User clicks Replay
    controller.replay_alert(high_risk_result)
    assert controller.audio_count == 2


def test_browser_audio_restriction_fallback():
    """Verify browser autoplay policy blocks or Web Audio failures are handled gracefully."""
    restricted_controller = AudioAlertControllerMock(autoplay_blocked=True)

    high_risk_result = {
        "case_id": "CASE-RESTRICTED-001",
        "decision": "BLOCK",
        "risk_score": 90.0
    }

    restricted_controller.receive_detection_result(high_risk_result)
    assert restricted_controller.audio_count == 0
    assert restricted_controller.audio_status == "RESTRICTED"
    # Visual warning remains intact and valid
    assert is_high_risk_alert_verdict(high_risk_result) is True


def test_no_trigger_on_loading_states_or_errors():
    """Verify audio does NOT trigger on loading states or transient errors."""
    controller = AudioAlertControllerMock()

    # While analyzing
    dummy_result = {"decision": "BLOCK", "risk_score": 90.0}
    controller.receive_detection_result(dummy_result, is_analyzing=True)
    assert controller.audio_count == 0

    # Null / empty
    controller.receive_detection_result(None)
    assert controller.audio_count == 0


# ---------------------------------------------------------------------------
# Integration Tests: End-to-End API Forensics & Validation Failures
# ---------------------------------------------------------------------------

def test_api_check_payment_high_risk_verdict_integration():
    """Integration: Phishing QR payload produces authoritative BLOCK and HIGH RISK verdict."""
    payload = {
        "input_type": "LINK",
        "payload": "https://secure-hdfc-kyc.top/verify?user=8801",
        "scenario_id": "SCENARIO_2_SUSPICIOUS_PHISHING",
        "allow_external_threat_lookup": False
    }
    res = client.post("/api/check-payment", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["decision"] in ["BLOCK", "STEP_UP"]
    assert data["risk_score"] >= 70.0
    assert is_high_risk_alert_verdict(data) is True


def test_api_check_payment_benign_verdict_integration():
    """Integration: Clean verified retail UPI QR produces APPROVE verdict without alert."""
    payload = {
        "input_type": "QR",
        "payload": "upi://pay?pa=freshmart.retail@icici&pn=Fresh%20Mart%20Retail&am=850.00&cu=INR&tn=Order%204991",
        "allow_external_threat_lookup": False
    }
    res = client.post("/api/check-payment", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["decision"] == "APPROVE"
    assert data["risk_score"] < 40.0
    assert is_high_risk_alert_verdict(data) is False


def test_api_validation_failure_handling():
    """Verify bad requests (e.g. invalid JSON or missing types) fail with 422 Unprocessable Entity."""
    # Empty body
    res = client.post("/api/check-payment", json={})
    # CheckPaymentRequest has default input_type="QR", but predict requires txn fields
    res_predict = client.post("/api/predict", json={})
    assert res_predict.status_code == 422


def test_text_forensics_zero_width_and_homoglyphs():
    """Unit: ThreatIntelligenceService detects zero-width obfuscation and mixed-script homoglyphs."""
    from backend.app.services.threat_intel_service import threat_intel_service
    
    # 1. Zero-width character obfuscation
    obfuscated_url = "https://pay\u200btm.com"
    norm_res = threat_intel_service.sanitize_and_normalize_text(obfuscated_url)
    assert norm_res["has_zero_width"] is True
    assert norm_res["zero_width_count"] == 1
    assert norm_res["normalized_text"] == "https://paytm.com"

    # 2. Cyrillic homoglyph (а is Cyrillic \u0430)
    cyrillic_spoof = "pаytm"
    homo_res = threat_intel_service.sanitize_and_normalize_text(cyrillic_spoof)
    assert homo_res["has_homoglyphs"] is True
    assert "CYRILLIC" in homo_res["detected_scripts"]


def test_file_upload_forensics_integration():
    """Integration: File metadata and SHA-256 seal extraction for non-image artifacts."""
    import base64
    fake_pdf_content = b"%PDF-1.5 \n%Fake payment receipt payload\n"
    b64_pdf = base64.b64encode(fake_pdf_content).decode("utf-8")

    payload = {
        "input_type": "FILE",
        "image_base64": b64_pdf,
        "filename": "tax_invoice_2026.pdf",
        "allow_external_threat_lookup": False
    }
    res = client.post("/api/check-payment", json=payload)
    assert res.status_code == 200
    data = res.json()

    evidence_fields = [e["field"] for e in data.get("evidence", [])]
    assert "sha256_hash" in evidence_fields
    assert "file_detected_type" in evidence_fields
    
    # Check file type detection
    file_type_ev = next(e for e in data["evidence"] if e["field"] == "file_detected_type")
    assert file_type_ev["value"] == "DOCUMENT_PDF"

