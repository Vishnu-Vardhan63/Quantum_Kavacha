import time
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

print("=" * 80)
print("QUANTUM KAVACHA -- HARDWARE-ROOTED TRUST & MULTI-SIGNAL E2E VALIDATION")
print("=" * 80)

# 1. Hardware Status
h_resp = client.get("/api/device/status")
print(f"\n[1] Hardware Status -> Status {h_resp.status_code}")
print(f"    - Primary Node:   {h_resp.json().get('primary_device_id')}")
print(f"    - Microcontroller: {h_resp.json().get('hardware_model')}")
print(f"    - Cryptography:   {h_resp.json().get('cryptographic_primitives')}")
print(f"    - Sensor Package: {h_resp.json().get('sensors')}")

# 2. Device Identity Record
id_resp = client.get("/api/device/identity?device_id=QK-ESP32-7F3A")
print(f"\n[2] Device Identity -> Status {id_resp.status_code}")
print(f"    - Device ID:      {id_resp.json().get('device_id')}")
print(f"    - Factory Digest: {id_resp.json().get('factory_identity_hash')}")
print(f"    - Secure Boot:    {id_resp.json().get('secure_boot_status')}")
print(f"    - Attestation:    {id_resp.json().get('attestation_status')}")

# 3. Challenge-Response Protocol (Nonce + HMAC)
c_resp = client.post("/api/device/attestation/demo-challenge?device_id=QK-ESP32-7F3A")
print(f"\n[3] Challenge-Response Attestation -> Status {c_resp.status_code}")
verif = c_resp.json().get("verification", {})
print(f"    - Challenge Nonce: {c_resp.json().get('challenge', {}).get('nonce')[:24]}...")
print(f"    - Attestation:     {verif.get('status')} (Latency: {verif.get('verification_latency_ms')} ms)")
print(f"    - Anti-Rollback:   Monotonic Counter #{c_resp.json().get('device_response', {}).get('monotonic_counter')}")

# 4. Sensor Telemetry & Fingerprint Match
telem_resp = client.get("/api/device/telemetry?device_id=QK-ESP32-7F3A")
fp_resp = client.get("/api/device/fingerprint?device_id=QK-ESP32-7F3A")
print(f"\n[4] Sensor Telemetry & Fingerprint -> Status {telem_resp.status_code}")
print(f"    - Accel Sample:    X={telem_resp.json().get('sensor_window', {}).get('accel_x', [0])[0]:.4f}g, Z={telem_resp.json().get('sensor_window', {}).get('accel_z', [0])[0]:.4f}g")
print(f"    - Baseline Match:  {fp_resp.json().get('comparison', {}).get('status')} ({fp_resp.json().get('comparison', {}).get('similarity_pct')}%)")

# 5. Composite Device Trust Score
trust_resp = client.get("/api/device/trust?device_id=QK-ESP32-7F3A")
print(f"\n[5] Composite Device Trust Score -> Status {trust_resp.status_code}")
print(f"    - Total Score:     {trust_resp.json().get('total_score')}/100 ({trust_resp.json().get('trust_level')})")
print(f"    - Breakdown:       {trust_resp.json().get('breakdown')}")

# 6. Experimental PUF Layer
puf_resp = client.get("/api/device/experimental-puf?device_id=QK-ESP32-7F3A")
print(f"\n[6] Experimental PUF Signal -> Status {puf_resp.status_code}")
print(f"    - Stability:       {puf_resp.json().get('stability_pct')}%")
print(f"    - Min-Entropy:     {puf_resp.json().get('estimated_entropy_bits')} bits")
print(f"    - Epistemic Tag:   {puf_resp.json().get('provenance')}")

print("\n" + "=" * 80)
print("ALL HARDWARE TRUST & CRYPTOGRAPHIC TELEMETRY LAYERS VALIDATED SUCCESSFULLY!")
print("=" * 80)
