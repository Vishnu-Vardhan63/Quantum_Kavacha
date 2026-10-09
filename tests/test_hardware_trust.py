import pytest
import hmac
import hashlib
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.hardware_trust_service import hardware_trust_service
from backend.app.schemas.hardware_trust import AttestationVerificationRequest, SensorWindow

client = TestClient(app)

def test_hardware_status_endpoint():
    resp = client.get("/api/device/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["primary_device_id"] == "QK-ESP32-7F3A"
    assert data["provenance"] == "HARDWARE_ATTESTED"
    assert "HMAC-SHA256 (eFuse)" in data["cryptographic_primitives"]

def test_device_identity_endpoint():
    resp = client.get("/api/device/identity?device_id=QK-ESP32-7F3A")
    assert resp.status_code == 200
    data = resp.json()
    assert data["device_id"] == "QK-ESP32-7F3A"
    assert data["hardware_class"].startswith("ESP32-S3")
    assert data["attestation_status"] == "VERIFIED"
    assert data["identity_confidence"] >= 0.90

def test_challenge_response_attestation_flow():
    # 1. Create challenge
    c_resp = client.post("/api/device/challenge", json={"device_id": "QK-ESP32-7F3A"})
    assert c_resp.status_code == 200
    chal = c_resp.json()
    assert "challenge_id" in chal
    assert len(chal["nonce"]) == 64  # 32 bytes hex

    # 2. Simulate hardware computation of HMAC
    req = hardware_trust_service.generate_simulated_device_attestation_response("QK-ESP32-7F3A", hardware_trust_service.create_challenge("QK-ESP32-7F3A"))
    
    # 3. Verify
    v_resp = client.post("/api/device/attestation/verify", json=req.model_dump())
    assert v_resp.status_code == 200
    v_data = v_resp.json()
    assert v_data["verified"] is True
    assert v_data["status"] == "VERIFIED"
    assert v_data["provenance"] == "HARDWARE_ATTESTED"

def test_replay_attack_prevention():
    # 1. Generate challenge & response
    chal = hardware_trust_service.create_challenge("QK-ESP32-7F3A")
    req = hardware_trust_service.generate_simulated_device_attestation_response("QK-ESP32-7F3A", chal)
    
    # 2. First submission must succeed
    v1 = hardware_trust_service.verify_attestation(req)
    assert v1.verified is True
    assert v1.status == "VERIFIED"

    # 3. Replay of the exact same nonce/request must fail with REPLAY_DETECTED
    v2 = hardware_trust_service.verify_attestation(req)
    assert v2.verified is False
    assert v2.status == "REPLAY_DETECTED"
    assert "REPLAY ATTACK PREVENTED" in v2.message

def test_sensor_fingerprint_baseline_and_matching():
    # 1. Extract baseline
    win_normal = SensorWindow(
        accel_x=[0.012, 0.013, 0.011],
        accel_y=[-0.034, -0.033, -0.035],
        accel_z=[0.982, 0.981, 0.983],
        gyro_x=[0.002, 0.001, 0.002],
        gyro_y=[0.001, 0.002, 0.001],
        gyro_z=[-0.001, -0.001, -0.002],
        mag_x=[22.4, 22.5, 22.3],
        mag_y=[-14.8, -14.7, -14.9],
        mag_z=[41.2, 41.1, 41.3]
    )
    fp_normal = hardware_trust_service.extract_sensor_fingerprint(win_normal)
    assert len(fp_normal.normalized_vector) == 9
    
    # Compare with enrolled primary baseline
    comp = hardware_trust_service.compare_sensor_fingerprint("QK-ESP32-7F3A", fp_normal)
    assert comp.status in ["MATCH", "PARTIAL_MATCH"]
    assert comp.similarity_pct >= 85.0

    # 2. Extract anomalous / displaced sensor window (e.g. emulator or altered physical device)
    win_anomaly = SensorWindow(
        accel_x=[0.85, 0.92, 0.78],
        accel_y=[0.40, 0.35, 0.45],
        accel_z=[0.10, 0.12, 0.08],
        gyro_x=[0.25, 0.30, 0.22],
        gyro_y=[0.18, 0.22, 0.19],
        gyro_z=[0.40, 0.38, 0.42],
        mag_x=[2.1, 2.0, 2.2],
        mag_y=[80.0, 81.2, 79.8],
        mag_z=[5.0, 4.8, 5.2]
    )
    fp_anomaly = hardware_trust_service.extract_sensor_fingerprint(win_anomaly)
    comp_anomaly = hardware_trust_service.compare_sensor_fingerprint("QK-ESP32-7F3A", fp_anomaly)
    assert comp_anomaly.status == "MISMATCH"
    assert comp_anomaly.similarity_pct < 70.0

def test_timing_drift_analysis():
    t_normal = hardware_trust_service.analyze_timing("2026-10-08T22:00:00Z", "2026-10-08T22:00:00.180Z", rtt_ms=45.0)
    assert t_normal.status == "NORMAL"

    t_anomaly = hardware_trust_service.analyze_timing("2026-10-08T21:58:00Z", "2026-10-08T22:00:00Z", rtt_ms=650.0)
    assert t_anomaly.status == "TIMING_ANOMALY"

def test_device_trust_score_breakdown():
    resp = client.get("/api/device/trust?device_id=QK-ESP32-7F3A")
    assert resp.status_code == 200
    score_data = resp.json()
    assert score_data["total_score"] >= 75.0
    assert score_data["trust_level"] == "TRUSTED"
    assert "hardware_identity" in score_data["breakdown"]
    assert "cryptographic_attestation" in score_data["breakdown"]
    assert "sensor_fingerprint" in score_data["breakdown"]

def test_experimental_puf_signal():
    resp = client.get("/api/device/experimental-puf?device_id=QK-ESP32-7F3A")
    assert resp.status_code == 200
    puf = resp.json()
    assert puf["provenance"] == "EXPERIMENTAL"
    assert "stability_pct" in puf
    assert puf["stability_pct"] >= 90.0

def test_demo_challenge_endpoint():
    resp = client.post("/api/device/attestation/demo-challenge?device_id=QK-ESP32-7F3A")
    assert resp.status_code == 200
    res = resp.json()
    assert res["verification"]["verified"] is True
    assert res["verification"]["status"] == "VERIFIED"

def test_hardware_tamper_simulation():
    # 1. Tamper device
    t_resp = client.post("/api/device/simulate-tamper", json={"device_id": "QK-ESP32-7F3A"})
    assert t_resp.status_code == 200
    
    # 2. Check identity now reports FAILED
    id_resp = client.get("/api/device/identity?device_id=QK-ESP32-7F3A")
    assert id_resp.json()["attestation_status"] == "FAILED"
    assert id_resp.json()["secure_boot_status"] == "DISABLED"

    # 3. Reset state
    r_resp = client.post("/api/device/reset", json={"device_id": "QK-ESP32-7F3A"})
    assert r_resp.status_code == 200
    id_resp2 = client.get("/api/device/identity?device_id=QK-ESP32-7F3A")
    assert id_resp2.json()["attestation_status"] == "VERIFIED"
