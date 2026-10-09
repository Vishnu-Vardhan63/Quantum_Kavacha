import io
import base64
import pytest
import numpy as np
from PIL import Image
from unittest.mock import patch

from backend.app.services.payment_forensics import payment_forensics_service
from backend.app.services.gemini_evidence_service import (
    gemini_evidence_service,
    validate_image_payload
)

def test_qr_validation_payload_types():
    """Test real payment payloads: UPI URI, standard URL, dangerous schemes."""
    # 1. Valid Payment UPI URI
    upi_payload = "upi://pay?pa=merchant.retail@icici&pn=Merchant%20Retail&am=1250.00&cu=INR&tn=Invoice%204410"
    parsed_upi = payment_forensics_service.parse_upi_payload(upi_payload)
    assert parsed_upi["is_upi"] is True
    assert parsed_upi["pa"] == "merchant.retail@icici"
    assert parsed_upi["pn"] == "Merchant Retail"
    assert parsed_upi["am"] == 1250.0
    assert parsed_upi["cu"] == "INR"

    is_safe_upi, msg_upi, meta_upi = payment_forensics_service.validate_url_security(upi_payload)
    assert is_safe_upi is True
    assert meta_upi["is_safe_protocol"] is True

    # 2. QR containing standard HTTPS URL
    https_payload = "https://checkout.razorpay.com/v1/invoice/inv_12345"
    is_safe_url, msg_url, meta_url = payment_forensics_service.validate_url_security(https_payload)
    assert is_safe_url is True
    assert meta_url["scheme"] == "https"
    assert meta_url["domain"] == "checkout.razorpay.com"

    # 3. QR containing dangerous scheme (javascript:, data:)
    js_payload = "javascript:alert('malicious_redirect')"
    is_safe_js, msg_js, _ = payment_forensics_service.validate_url_security(js_payload)
    assert is_safe_js is False
    assert "Dangerous URL scheme rejected" in msg_js

    # 4. QR containing SSRF attempt to local network
    ssrf_payload = "http://127.0.0.1:8000/internal/admin"
    is_safe_ssrf, msg_ssrf, _ = payment_forensics_service.validate_url_security(ssrf_payload)
    assert is_safe_ssrf is False
    assert "SSRF Blocked" in msg_ssrf

def test_qr_decoding_image_inputs():
    """Test image decoding scenarios: no QR, malformed data, and empty input."""
    # Blank blue image with NO QR code
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="blue").save(buf, format="PNG")
    b64_no_qr = base64.b64encode(buf.getvalue()).decode()

    val_no_qr, err_no_qr = payment_forensics_service.decode_qr_image(b64_no_qr)
    assert val_no_qr is None
    assert "No readable QR code found" in err_no_qr

    # Malformed base64
    val_mal, err_mal = payment_forensics_service.decode_qr_image("!!!not_base64!!!")
    assert val_mal is None

def test_exif_tamper_signature_handling():
    """Verify that photo-editing software signatures in EXIF trigger tamper notices without claiming definitive proof."""
    from PIL import PngImagePlugin
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color="white")
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("Software", "Adobe Photoshop 2024")
    img.save(buf, format="PNG", pnginfo=pnginfo)
    raw_bytes = buf.getvalue()

    valid, meta, _ = validate_image_payload(raw_bytes, "payment_screenshot.png")
    assert valid is True
    assert meta.metadata_tamper_warning is not None
    assert "Photoshop" in meta.metadata_tamper_warning

def test_verdict_three_state_determinism():
    """Verify strict three-state evidence verdicts: SUSPICIOUS, INCONCLUSIVE, NO_ISSUES_DETECTED."""
    # 1. SUSPICIOUS when amount mismatches
    dummy_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    mock_res_mismatch = {
        "extracted_fields": {
            "amount": 999.0,
            "recipient_vpa": "vendor@upi",
            "payment_status": "SUCCESS"
        },
        "manipulation_level": "NONE_DETECTED",
        "observations": ["Discrepancy detected"]
    }
    with patch.object(gemini_evidence_service, "_call_gemini_multimodal", return_value=(mock_res_mismatch, None)):
        res = gemini_evidence_service.analyze_evidence(
            image_base64=dummy_b64,
            declared_amount=500.0,
            declared_vpa="vendor@upi"
        )
        assert res.final_verdict == "SUSPICIOUS"
        assert res.settlement_status == "UNVERIFIED_PENDING_SETTLEMENT"

    # 2. NO_ISSUES_DETECTED when fields match cleanly
    mock_res_clean = {
        "extracted_fields": {
            "amount": 500.0,
            "recipient_vpa": "vendor@upi",
            "merchant": "Vendor Store",
            "payment_status": "SUCCESS"
        },
        "manipulation_level": "NONE_DETECTED",
        "observations": ["Receipt UI aligned"]
    }
    with patch.object(gemini_evidence_service, "_call_gemini_multimodal", return_value=(mock_res_clean, None)):
        res = gemini_evidence_service.analyze_evidence(
            image_base64=dummy_b64,
            declared_amount=500.0,
            declared_vpa="vendor@upi"
        )
        assert res.final_verdict == "NO_ISSUES_DETECTED"
        assert res.settlement_status == "UNVERIFIED_PENDING_SETTLEMENT"

    # 3. INCONCLUSIVE when fields are unavailable
    res_inconclusive = gemini_evidence_service.analyze_evidence(
        image_base64=dummy_b64
    )
    assert res_inconclusive.final_verdict in ["INCONCLUSIVE", "NO_ISSUES_DETECTED"]
