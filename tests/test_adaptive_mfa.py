import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.adaptive_mfa_service import adaptive_mfa_service
from backend.app.schemas.adaptive_mfa import MFAVerificationSubmission
from backend.app.services.hardware_trust_service import hardware_trust_service

client = TestClient(app)

def test_adaptive_mfa_level_0_passive():
    """Verify clean transaction with trusted hardware receives Level 0 Passive approval."""
    res = adaptive_mfa_service.evaluate_adaptive_mfa(
        case_id="CASE-CLEAN-001",
        user_id="USR-1001",
        device_id="QK-ESP32-7F3A",
        risk_score=15.0,
        device_trust_score=94.0
    )
    assert res.auth_level == 0
    assert res.auth_level_label == "LEVEL_0_PASSIVE"
    assert res.decision == "APPROVE"
    assert res.status == "VERIFIED"
    assert len(res.explanation.factor_contributions) >= 1
    assert res.explanation.factor_contributions[0].factor_name == "Base Transaction Profile"

def test_adaptive_mfa_level_1_possession_otp():
    """Verify moderate risk transaction triggers Level 1 Possession / OTP."""
    res = adaptive_mfa_service.evaluate_adaptive_mfa(
        case_id="CASE-MOD-001",
        user_id="USR-1001",
        device_id="QK-ESP32-7F3A",
        risk_score=48.0,
        device_trust_score=85.0
    )
    assert res.auth_level == 1
    assert res.auth_level_label == "LEVEL_1_POSSESSION_OTP"
    assert res.decision == "STEP_UP_REQUIRED"
    assert res.otp_masked_destination is not None

def test_adaptive_mfa_level_2_strong_passkey():
    """Verify elevated risk transaction triggers Level 2 Strong Passkey / WebAuthn."""
    res = adaptive_mfa_service.evaluate_adaptive_mfa(
        case_id="CASE-HIGH-001",
        user_id="USR-1001",
        device_id="QK-ESP32-7F3A",
        risk_score=72.0,
        device_trust_score=70.0
    )
    assert res.auth_level == 2
    assert res.auth_level_label == "LEVEL_2_STRONG_PASSKEY"
    assert res.decision == "STEP_UP_REQUIRED"
    assert res.passkey_challenge is not None
    assert "challenge" in res.passkey_challenge

def test_adaptive_mfa_level_3_hardware_attestation():
    """Verify hardware failure or critical risk triggers Level 3 ESP32-S3 Attestation."""
    res = adaptive_mfa_service.evaluate_adaptive_mfa(
        case_id="CASE-CRIT-001",
        user_id="USR-1001",
        device_id="QK-ESP32-7F3A",
        risk_score=88.0,
        device_trust_score=42.0,
        payload_integrity={"status": "MISMATCH"}
    )
    assert res.auth_level == 3
    assert res.auth_level_label == "LEVEL_3_HARDWARE_ATTESTATION"
    assert res.challenge_payload is not None
    assert "nonce" in res.challenge_payload
    assert len(res.explanation.factor_contributions) >= 3

def test_mfa_verification_otp_flow():
    """Verify OTP verification flow."""
    eval_res = adaptive_mfa_service.evaluate_adaptive_mfa(
        case_id="CASE-OTP-001",
        user_id="USR-1001",
        device_id="QK-ESP32-7F3A",
        risk_score=45.0,
        device_trust_score=85.0
    )
    # Valid OTP
    sub_valid = MFAVerificationSubmission(
        auth_session_id=eval_res.auth_session_id,
        case_id=eval_res.case_id,
        auth_type="OTP",
        otp_code="739218"
    )
    res_valid = adaptive_mfa_service.verify_mfa_submission(sub_valid)
    assert res_valid.verified is True
    assert res_valid.final_decision == "APPROVE"

    # Invalid OTP
    sub_invalid = MFAVerificationSubmission(
        auth_session_id=eval_res.auth_session_id,
        case_id=eval_res.case_id,
        auth_type="OTP",
        otp_code="00"
    )
    res_invalid = adaptive_mfa_service.verify_mfa_submission(sub_invalid)
    assert res_invalid.verified is False
    assert res_invalid.final_decision == "BLOCK"

def test_mfa_verification_hardware_flow():
    """Verify Level 3 Hardware Attestation challenge-response verification."""
    eval_res = adaptive_mfa_service.evaluate_adaptive_mfa(
        case_id="CASE-HW-001",
        user_id="USR-1001",
        device_id="QK-ESP32-7F3A",
        risk_score=85.0,
        device_trust_score=45.0
    )
    chal_id = eval_res.challenge_payload["challenge_id"]
    chal_obj = hardware_trust_service.create_challenge("QK-ESP32-7F3A")
    # Re-evaluate with this challenge ID
    eval_res.challenge_payload = chal_obj.model_dump()
    req = hardware_trust_service.generate_simulated_device_attestation_response("QK-ESP32-7F3A", chal_obj)

    sub_hw = MFAVerificationSubmission(
        auth_session_id=eval_res.auth_session_id,
        case_id=eval_res.case_id,
        auth_type="HARDWARE_CHALLENGE",
        hardware_challenge_id=req.challenge_id,
        hardware_nonce=req.nonce,
        hardware_hmac_response=req.hmac_response,
        firmware_hash=req.firmware_hash,
        monotonic_counter=req.monotonic_counter,
        timestamp_utc=req.timestamp_utc
    )
    res_hw = adaptive_mfa_service.verify_mfa_submission(sub_hw)
    assert res_hw.verified is True
    assert res_hw.final_decision == "APPROVE"
    assert res_hw.provenance == "HARDWARE_ATTESTED"

def test_mfa_api_endpoints():
    """Verify HTTP REST endpoints for MFA evaluate and verify."""
    resp = client.post("/api/v1/mfa/evaluate", json={
        "case_id": "CASE-API-001",
        "user_id": "USR-1001",
        "device_id": "QK-ESP32-7F3A",
        "risk_score": 52.0,
        "device_trust_score": 88.0
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "auth_session_id" in data
    assert data["auth_level"] == 1

    # Verify endpoint
    v_resp = client.post("/api/v1/mfa/verify", json={
        "auth_session_id": data["auth_session_id"],
        "case_id": data["case_id"],
        "auth_type": "OTP",
        "otp_code": "739218"
    })
    assert v_resp.status_code == 200
    v_data = v_resp.json()
    assert v_data["verified"] is True
