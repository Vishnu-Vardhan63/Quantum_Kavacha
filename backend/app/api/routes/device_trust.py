from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, List, Optional

from backend.app.schemas.hardware_trust import (
    DeviceIdentityRecord,
    CryptographicChallenge,
    AttestationVerificationRequest,
    AttestationVerificationResponse,
    SensorWindow,
    SensorFingerprint,
    SensorComparisonResult,
    DeviceTimingAnalysis,
    ExperimentalPUFSignal,
    DeviceTrustScore,
    DeviceTelemetryPacket,
    AutoVerifyPaymentRequest,
    AutoVerifyPaymentResponse,
    DelayedRecheckRequest,
    DelayedRecheckResponse,
    OnePressFraudReportRequest,
    OnePressFraudReportResponse,
    DynamicQRRequest,
    DynamicQRResponse,
    DynamicQRVerifyRequest,
    DynamicQRVerifyResponse
)
from backend.app.services.hardware_trust_service import hardware_trust_service

router = APIRouter(prefix="/api/device", tags=["Hardware Trust & Attestation"])

@router.get("/status", summary="Get Hardware Node Status")
def get_hardware_status():
    devices = hardware_trust_service.list_devices()
    primary = hardware_trust_service.get_device_identity("QK-ESP32-7F3A")
    return {
        "service": "QUANTUM KAVACHA Hardware Trust Node",
        "primary_device_id": "QK-ESP32-7F3A",
        "hardware_model": "ESP32-S3-DevKitC-1",
        "nodes_online": sum(1 for d in devices if d.get("is_online")),
        "attestation_engine": "ACTIVE",
        "cryptographic_primitives": ["HMAC-SHA256 (eFuse)", "Secure Boot v2 (RSA-3072)", "Flash Encryption (AES-256-XTS)"],
        "sensors": ["MPU6050 (6-axis IMU)", "QMC5883L (3-axis Magnetometer)", "BME280 (Temp/Humidity/Pressure)"],
        "provenance": "HARDWARE_ATTESTED",
        "devices": devices
    }

@router.get("/identity", response_model=DeviceIdentityRecord, summary="Get Active Device Identity")
def get_device_identity(device_id: str = Query("QK-ESP32-7F3A")):
    rec = hardware_trust_service.get_device_identity(device_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not registered")
    return rec

@router.post("/challenge", response_model=CryptographicChallenge, summary="Generate Cryptographic Challenge Nonce")
def create_challenge(payload: Dict[str, Any] = Body(default={})):
    dev_id = payload.get("device_id", "QK-ESP32-7F3A")
    return hardware_trust_service.create_challenge(dev_id)

@router.post("/attestation/verify", response_model=AttestationVerificationResponse, summary="Verify Device Attestation Response")
def verify_attestation(req: AttestationVerificationRequest):
    return hardware_trust_service.verify_attestation(req)

@router.post("/attestation/demo-challenge", summary="Interactive One-Click Challenge & Verification Demo")
def demo_challenge(device_id: str = Query("QK-ESP32-7F3A")):
    """
    Complete end-to-end challenge-response demo for UI.
    Generates nonce -> Hardware calculates HMAC -> Backend verifies digest.
    """
    chal = hardware_trust_service.create_challenge(device_id)
    req = hardware_trust_service.generate_simulated_device_attestation_response(device_id, chal)
    verif = hardware_trust_service.verify_attestation(req)
    return {
        "challenge": chal,
        "device_response": req,
        "verification": verif
    }

@router.get("/telemetry", response_model=DeviceTelemetryPacket, summary="Get Live Device Sensor Telemetry")
def get_telemetry(device_id: str = Query("QK-ESP32-7F3A")):
    return hardware_trust_service.get_live_telemetry(device_id)

@router.get("/fingerprint", summary="Get Device Sensor Fingerprint vs Baseline")
def get_fingerprint(device_id: str = Query("QK-ESP32-7F3A")):
    packet = hardware_trust_service.get_live_telemetry(device_id)
    current_fp = hardware_trust_service.extract_sensor_fingerprint(packet.sensor_window)
    comp = hardware_trust_service.compare_sensor_fingerprint(device_id, current_fp)
    baseline = hardware_trust_service._sensor_baselines.get(device_id)
    return {
        "device_id": device_id,
        "current_fingerprint": current_fp,
        "enrolled_baseline": baseline,
        "comparison": comp
    }

@router.get("/trust", response_model=DeviceTrustScore, summary="Compute Composite Device Trust Score")
def get_device_trust(device_id: str = Query("QK-ESP32-7F3A")):
    packet = hardware_trust_service.get_live_telemetry(device_id)
    current_fp = hardware_trust_service.extract_sensor_fingerprint(packet.sensor_window)
    comp = hardware_trust_service.compare_sensor_fingerprint(device_id, current_fp)
    return hardware_trust_service.compute_device_trust_score(
        device_id=device_id,
        sensor_result=comp,
        timing_analysis=packet.timing
    )

@router.post("/enroll", summary="Enroll & Register New Hardware Trust Node")
def enroll_device(payload: Dict[str, Any] = Body(...)):
    dev_id = payload.get("device_id", f"QK-ESP32-{secrets.token_hex(2).upper()}")
    hw_class = payload.get("hardware_class", "ESP32-S3-DevKitC-1")
    hardware_trust_service._devices[dev_id] = {
        "device_id": dev_id,
        "hardware_class": hw_class,
        "factory_identity_hash": secrets.token_hex(32),
        "firmware_version": "1.0.4-release",
        "firmware_hash": secrets.token_hex(32),
        "secure_boot_status": "ENABLED",
        "flash_encryption_status": "ENABLED",
        "hmac_status": "AVAILABLE",
        "digital_signature_status": "AVAILABLE",
        "sensor_package": "IMU + MAGNETOMETER + BME280",
        "attestation_status": "VERIFIED",
        "identity_confidence": 0.95,
        "provenance": "HARDWARE_ATTESTED",
        "is_online": True,
        "is_tampered": False,
        "uptime_sec": 100,
        "rssi_dbm": -55,
        "battery_mv": 3300,
        "temperature_c": 27.5
    }
    hardware_trust_service._device_keys[dev_id] = secrets.token_bytes(32)
    hardware_trust_service._device_monotonic_counters[dev_id] = 1000
    hardware_trust_service.enroll_sensor_baseline(dev_id, [])

    return {
        "status": "ENROLLED_SUCCESSFULLY",
        "device_id": dev_id,
        "trust_node": hardware_trust_service.get_device_identity(dev_id)
    }

@router.post("/simulate-tamper", summary="Simulate Firmware Tampering / Attestation Failure")
def simulate_tamper(payload: Dict[str, Any] = Body(default={})):
    dev_id = payload.get("device_id", "QK-ESP32-7F3A")
    return hardware_trust_service.simulate_tamper(dev_id)

@router.post("/simulate-disconnect", summary="Simulate Hardware Node Disconnect")
def simulate_disconnect(payload: Dict[str, Any] = Body(default={})):
    dev_id = payload.get("device_id", "QK-ESP32-7F3A")
    return hardware_trust_service.simulate_disconnect(dev_id)

@router.post("/reset", summary="Reset Device State to Nominal Baseline")
def reset_device(payload: Dict[str, Any] = Body(default={})):
    dev_id = payload.get("device_id", "QK-ESP32-7F3A")
    return hardware_trust_service.reset_device_state(dev_id)

@router.get("/experimental-puf", response_model=ExperimentalPUFSignal, summary="Get Experimental PUF Research Signal")
def get_puf_signal(device_id: str = Query("QK-ESP32-7F3A")):
    return hardware_trust_service.get_experimental_puf_signal(device_id)

# --------------------------------------------------------------------------
# Official Team Lead ESP32 Gateway Endpoints
# --------------------------------------------------------------------------

@router.post("/auto-verify-payment", response_model=AutoVerifyPaymentResponse, summary="Auto-Verify Payment via ESP32 Trust Gateway")
def auto_verify_payment(req: AutoVerifyPaymentRequest):
    """
    Primary ESP32 Payment Verification Endpoint.
    Merchant presses 'VERIFY PAYMENT' on ESP32 or UI.
    Evaluates payment record, multi-modal evidence, ESP32 attestation, and outputs 4-tier LED & Voice alert.
    """
    return hardware_trust_service.auto_verify_payment(req)

@router.post("/delayed-recheck", response_model=DelayedRecheckResponse, summary="Delayed Payment Settlement Recheck (~2 min)")
def delayed_recheck(req: DelayedRecheckRequest):
    """
    Scheduled settlement status recheck for chargebacks, reversals, and cancellations.
    """
    return hardware_trust_service.delayed_recheck_payment(req)

@router.post("/report-fraud", response_model=OnePressFraudReportResponse, summary="One-Press Physical Button Fraud Escalation")
def report_fraud_one_press(req: OnePressFraudReportRequest):
    """
    Physical 'REPORT FRAUD' button on ESP32 instantly opens an authoritative investigation case.
    """
    return hardware_trust_service.report_fraud_one_press(req)

@router.post("/dynamic-qr", response_model=DynamicQRResponse, summary="Generate Time-Bounded (30s) Signed Dynamic UPI QR")
def generate_dynamic_qr(req: DynamicQRRequest):
    """
    Generates dynamic signed QR payload with 30s TTL, cryptographic nonce, and signature digest.
    """
    return hardware_trust_service.generate_dynamic_qr(req)

@router.post("/dynamic-qr/verify", response_model=DynamicQRVerifyResponse, summary="Validate Scanned Dynamic QR Payload")
def verify_dynamic_qr(req: DynamicQRVerifyRequest):
    """
    Validates dynamic QR for expiration, signature integrity, and payload tampering.
    """
    return hardware_trust_service.verify_dynamic_qr(req)

@router.get("/edge-rules", summary="Get Offline Edge Deterministic Rules for Disconnected ESP32 Mode")
def get_edge_rules():
    """
    Returns offline edge safety rules when cloud connectivity is unavailable.
    """
    return hardware_trust_service.get_offline_edge_rules()

