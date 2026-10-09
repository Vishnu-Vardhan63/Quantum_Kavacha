import pytest
import base64
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.gemini_evidence_service import gemini_evidence_service

client = TestClient(app)

# Dummy 1x1 transparent PNG image base64
DUMMY_IMAGE_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

def test_evidence_analyze_without_image():
    """Verify endpoint gracefully handles request without image binary."""
    res = client.post("/api/evidence/analyze", json={})
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "Gemini Multimodal"
    assert data["analysis_status"] == "UNAVAILABLE"
    assert data["overall_evidence_confidence"] == "UNAVAILABLE"

def test_evidence_analyze_fallback_mode():
    """Verify deterministic fallback when Gemini API key is offline/unconfigured."""
    res = client.post("/api/evidence/analyze", json={
        "image_base64": DUMMY_IMAGE_B64,
        "declared_amount": 2500.0,
        "declared_vpa": "store@icici"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "Gemini Multimodal"
    assert "visual_assessment" in data
    assert "extracted_fields" in data
    assert "qr_cross_check" in data

    # Verify no fabricated values: AI likelihood must be null/None when unavailable
    assert data["visual_assessment"]["ai_generation_likelihood"] is None
    assert data["visual_assessment"]["ai_generation_assessment"] == "UNAVAILABLE"

def test_qr_screenshot_mismatch_detection():
    """Verify that amount/recipient mismatch between image and QR payload is cleanly flagged."""
    mock_gemini_response = {
        "ai_generation_likelihood": 12.0,
        "ai_generation_assessment": "LOW INDICATION",
        "manipulation_level": "HIGH",
        "manipulation_indicators": ["Font baseline mismatch on amount field", "Visible compression boundary around ₹4,999 text"],
        "image_integrity_score": 68.0,
        "visual_consistency_score": 70.0,
        "text_consistency_score": 65.0,
        "ui_authenticity_score": 75.0,
        "extracted_fields": {
            "amount": 4999.0,
            "recipient_vpa": "fakecare@ybl",
            "recipient_name": "Customer Care",
            "sender_name": "Victim User",
            "transaction_id": "TXN4991002341",
            "timestamp_text": "Today, 11:42 PM",
            "merchant": "ICICI Bank Care",
            "payment_status": "SUCCESS",
            "bank_or_app": "Google Pay",
            "reference_number": "REF9901"
        },
        "observations": ["Observed mismatched amount relative to standard checkout."],
        "limitations": ["Compressed image upload."]
    }

    with patch.object(gemini_evidence_service, "_call_gemini_multimodal", return_value=(mock_gemini_response, None)):
        res = client.post("/api/evidence/analyze", json={
            "image_base64": DUMMY_IMAGE_B64,
            "declared_amount": 499.0, # QR payload has ₹499 vs screenshot ₹4,999
            "declared_vpa": "fakecare@ybl"
        })
        assert res.status_code == 200
        data = res.json()

        assert data["analysis_status"] == "COMPLETED"
        assert data["visual_assessment"]["manipulation_level"] == "HIGH"
        assert len(data["visual_assessment"]["manipulation_indicators"]) >= 2
        assert data["visual_assessment"]["ai_generation_assessment"] == "LOW INDICATION"

        # Check amount mismatch detection
        amount_check = next((c for c in data["evidence_checks"] if c["field"] == "amount"), None)
        assert amount_check is not None
        assert amount_check["result"] == "MISMATCH"
        assert amount_check["impact"] == "CRITICAL"
        assert "₹4,999" in amount_check["description"]

        # Check system derived consistency
        assert data["qr_cross_check"]["amount_comparison"] == "MISMATCH"
        assert data["overall_evidence_confidence"] == "LOW"

def test_genuine_payment_evidence_consistency():
    """Verify genuine payment scenario yields high consistency without manipulation."""
    mock_clean_response = {
        "ai_generation_likelihood": 5.0,
        "ai_generation_assessment": "LOW INDICATION",
        "manipulation_level": "NONE_DETECTED",
        "manipulation_indicators": [],
        "image_integrity_score": 96.0,
        "visual_consistency_score": 94.0,
        "text_consistency_score": 95.0,
        "ui_authenticity_score": 95.0,
        "extracted_fields": {
            "amount": 2500.0,
            "recipient_vpa": "verified.store@icici",
            "recipient_name": "Verified Store Retail",
            "sender_name": "Customer",
            "transaction_id": "TXN88019920",
            "timestamp_text": "Today, 10:15 AM",
            "merchant": "Verified Store Retail",
            "payment_status": "SUCCESS",
            "bank_or_app": "PhonePe",
            "reference_number": "UTR88019"
        },
        "observations": ["Consistent typography and native Android UI alignment."],
        "limitations": []
    }

    with patch.object(gemini_evidence_service, "_call_gemini_multimodal", return_value=(mock_clean_response, None)):
        res = client.post("/api/evidence/analyze", json={
            "image_base64": DUMMY_IMAGE_B64,
            "declared_amount": 2500.0,
            "declared_vpa": "verified.store@icici"
        })
        assert res.status_code == 200
        data = res.json()

        assert data["analysis_status"] == "COMPLETED"
        assert data["visual_assessment"]["manipulation_level"] == "NONE_DETECTED"
        assert data["qr_cross_check"]["amount_comparison"] == "MATCH"
        assert data["qr_cross_check"]["recipient_comparison"] == "MATCH"
        assert data["overall_evidence_confidence"] == "HIGH"
        assert data["system_derived_consistency_score"] is not None
        assert data["system_derived_consistency_score"] >= 90.0

def test_check_payment_integration_with_evidence_verification():
    """Verify that Check a Payment incorporates Gemini Evidence Verification into risk fusion."""
    test_req = {
        "input_type": "SCREENSHOT",
        "payload": "URGENT: Suspended Account Notice. Pay ₹15,000 to desk@upi immediately.",
        "image_base64": DUMMY_IMAGE_B64,
        "transaction_context": {
            "amount": 15000.0,
            "user_id": "USR-TEST-EV",
            "device_id": "DEV-TEST-EV",
            "velocity_1h": 6,
            "device_score": 0.75,
            "location_score": 0.60,
            "merchant_risk": 0.85
        }
    }
    res = client.post("/api/check-payment", json=test_req)
    assert res.status_code == 200
    data = res.json()

    assert "evidence_verification" in data
    assert data["evidence_verification"] is not None
    assert data["evidence_verification"]["provider"] == "Gemini Multimodal"

    # Verify fraud decision remained active
    assert data["risk_score"] > 0
    assert data["decision"] in ["BLOCK", "STEP_UP", "MONITOR", "APPROVE"]
