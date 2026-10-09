import pytest
import time
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.hardware_trust_service import hardware_trust_service
from backend.app.schemas.hardware_trust import (
    AutoVerifyPaymentRequest, DelayedRecheckRequest, OnePressFraudReportRequest,
    DynamicQRRequest, DynamicQRVerifyRequest
)

client = TestClient(app)

def test_auto_verify_genuine_payment():
    """Verify clean retail payment receives VERIFIED, GREEN LED, and 'Payment verified.' voice alert."""
    hardware_trust_service.reset_device_state("QK-ESP32-7F3A")
    chal = hardware_trust_service.create_challenge("QK-ESP32-7F3A")
    req = hardware_trust_service.generate_simulated_device_attestation_response("QK-ESP32-7F3A", chal)

    resp = client.post("/api/device/auto-verify-payment", json={
        "transaction_id": "TX-RETAIL-1001",
        "merchant_id": "MERCHANT-ICICI-8801",
        "amount": 450.00,
        "device_id": "QK-ESP32-7F3A",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "nonce": req.nonce,
        "hmac_signature": req.hmac_response,
        "qr_payload": "upi://pay?pa=verified.store@icici&pn=Verified%20Store&am=450.00&cu=INR&tr=TX-RETAIL-1001"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["verification_status"] == "VERIFIED"
    assert data["decision"] == "APPROVE"
    assert data["led_state"] == "GREEN"
    assert data["voice_alert"] == "Payment verified."
    assert data["mfa_level"] == 0
    assert data["provenance"] == "HARDWARE_ATTESTED + MULTI_MODAL_VERIFIED"

def test_auto_verify_tampered_hardware():
    """Verify payment attempted from a tampered node triggers NOT_VERIFIED, RED_FLASH, and 'Payment blocked.'"""
    hardware_trust_service.simulate_tamper("QK-ESP32-7F3A")

    resp = client.post("/api/device/auto-verify-payment", json={
        "transaction_id": "TX-TAMPER-9901",
        "merchant_id": "MERCHANT-ICICI-8801",
        "amount": 25000.00,
        "device_id": "QK-ESP32-7F3A",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "nonce": "invalid_nonce_value",
        "hmac_signature": "invalid_hmac_signature"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["verification_status"] == "NOT_VERIFIED"
    assert data["decision"] == "BLOCK"
    assert data["led_state"] == "RED_FLASH"
    assert data["voice_alert"] == "Payment blocked."
    assert data["mfa_level"] == 3

    # Reset
    hardware_trust_service.reset_device_state("QK-ESP32-7F3A")

def test_delayed_recheck_workflow():
    """Verify delayed settlement recheck detects settled vs reversed transactions."""
    # 1. Normal settled payment
    resp1 = client.post("/api/device/delayed-recheck", json={
        "transaction_id": "TX-NORM-8821",
        "merchant_id": "MERCHANT-ICICI-8801",
        "device_id": "QK-ESP32-7F3A",
        "delay_seconds": 120
    })
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["settlement_status"] == "SETTLED"
    assert data1["alert_triggered"] is False
    assert data1["recheck_mode"] == "SIMULATED RECHECK"

    # 2. Reversal detected
    resp2 = client.post("/api/device/delayed-recheck", json={
        "transaction_id": "TX-REV-CHARGEBACK-4402",
        "merchant_id": "MERCHANT-ICICI-8801",
        "device_id": "QK-ESP32-7F3A",
        "delay_seconds": 120
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["settlement_status"] == "REVERSED"
    assert data2["alert_triggered"] is True
    assert "REVERSED" in data2["alert_details"]

def test_one_press_fraud_report():
    """Verify physical one-press fraud button opens an authoritative case in Investigation Center."""
    resp = client.post("/api/device/report-fraud", json={
        "device_id": "QK-ESP32-7F3A",
        "last_transaction_id": "TX-SUSP-7719",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "last_risk_score": 88.5,
        "last_decision": "BLOCK",
        "attestation_state": "FAILED",
        "merchant_notes": "Customer presented suspicious modified receipt visual"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "INVESTIGATION_OPENED"
    assert data["case_id"].startswith("QF-")
    assert len(data["recommended_actions"]) >= 3
    assert "investigation_url" in data

def test_dynamic_qr_lifecycle():
    """Verify dynamic QR generation, 30s TTL, and signature verification."""
    # 1. Generate dynamic QR
    gen_resp = client.post("/api/device/dynamic-qr", json={
        "merchant_id": "MERCHANT-ICICI-8801",
        "merchant_name": "Verified Store Retail",
        "merchant_vpa": "verified.store@icici",
        "amount": 850.00,
        "currency": "INR",
        "expiry_seconds": 30
    })
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    assert "upi://pay?" in gen_data["qr_payload"]
    assert gen_data["amount"] == 850.00
    assert len(gen_data["nonce"]) == 16
    assert len(gen_data["signature_digest"]) == 16

    # 2. Verify freshly generated QR
    v_resp = client.post("/api/device/dynamic-qr/verify", json={
        "qr_payload": gen_data["qr_payload"],
        "scanned_timestamp_utc": datetime.now(timezone.utc).isoformat()
    })
    assert v_resp.status_code == 200
    v_data = v_resp.json()
    assert v_data["valid"] is True
    assert v_data["status"] == "VALID"
    assert v_data["amount"] == 850.00

    # 3. Verify tampered amount in dynamic QR fails signature check
    tampered_payload = gen_data["qr_payload"].replace("am=850.00", "am=8500.00")
    t_resp = client.post("/api/device/dynamic-qr/verify", json={
        "qr_payload": tampered_payload,
        "scanned_timestamp_utc": datetime.now(timezone.utc).isoformat()
    })
    assert t_resp.status_code == 200
    t_data = t_resp.json()
    assert t_data["valid"] is False
    assert t_data["status"] == "SIGNATURE_MISMATCH"

def test_offline_edge_rules():
    """Verify offline edge safety parameters for disconnected ESP32 mode."""
    resp = client.get("/api/device/edge-rules")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "OFFLINE_SAFETY_MODE"
    assert data["max_offline_amount_inr"] == 2000.00
    assert "pa" in data["required_fields"]
    assert data["provenance"] == "HARDWARE_EDGE_POLICY"
