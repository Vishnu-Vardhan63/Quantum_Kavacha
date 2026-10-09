from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DeviceIdentityRecord(BaseModel):
    device_id: str = Field(..., description="Unique Hardware Device Identifier")
    hardware_class: str = Field("ESP32-S3-DevKitC-1", description="Microcontroller Hardware Model")
    factory_identity_hash: str = Field(..., description="SHA-256 Digest of eFuse MAC & Factory Block (Redacted)")
    firmware_version: str = Field("1.0.4-release", description="Active Firmware Release Version")
    secure_boot_status: str = Field("ENABLED", description="Secure Boot v2 Status (ENABLED/DISABLED/SIMULATED)")
    flash_encryption_status: str = Field("ENABLED", description="AES-256 XTS Flash Encryption Status")
    hmac_status: str = Field("AVAILABLE", description="Hardware-backed HMAC Peripheral Availability")
    digital_signature_status: str = Field("AVAILABLE", description="RSA/ECC Hardware DS Peripheral Availability")
    sensor_package: str = Field("IMU (MPU6050) + MAGNETOMETER (QMC5883L) + BME280", description="Connected Sensor Array")
    attestation_status: str = Field("VERIFIED", description="Cryptographic Attestation Status")
    identity_confidence: float = Field(0.96, description="Hardware Identity Confidence Score (0.0 - 1.0)")
    provenance: str = Field("HARDWARE_ATTESTED", description="Epistemic Origin Tag")

class CryptographicChallenge(BaseModel):
    challenge_id: str = Field(..., description="Unique Nonce Challenge Session Identifier")
    device_id: str = Field(..., description="Target Device Identifier")
    nonce: str = Field(..., description="Cryptographically Secure 256-bit Random Nonce Hex")
    timestamp_utc: str = Field(..., description="Challenge Generation Timestamp UTC")
    expires_at_utc: str = Field(..., description="Challenge Expiration Timestamp UTC")
    freshness_window_sec: int = Field(60, description="Freshness validity window in seconds")

class AttestationVerificationRequest(BaseModel):
    challenge_id: str
    device_id: str
    nonce: str
    hmac_response: str
    firmware_hash: str
    monotonic_counter: int
    timestamp_utc: str

class AttestationVerificationResponse(BaseModel):
    verified: bool
    status: str  # VERIFIED | FAILED | REPLAY_DETECTED | EXPIRED | UNKNOWN
    device_id: str
    challenge_id: str
    verification_latency_ms: float
    firmware_verified: bool
    monotonic_verified: bool
    provenance: str = "HARDWARE_ATTESTED"
    message: str

class SensorWindow(BaseModel):
    accel_x: List[float] = Field(default_factory=list)
    accel_y: List[float] = Field(default_factory=list)
    accel_z: List[float] = Field(default_factory=list)
    gyro_x: List[float] = Field(default_factory=list)
    gyro_y: List[float] = Field(default_factory=list)
    gyro_z: List[float] = Field(default_factory=list)
    mag_x: List[float] = Field(default_factory=list)
    mag_y: List[float] = Field(default_factory=list)
    mag_z: List[float] = Field(default_factory=list)
    temperature_c: Optional[float] = 28.4
    humidity_pct: Optional[float] = 52.1
    pressure_hpa: Optional[float] = 1013.2
    sampling_jitter_ms: Optional[float] = 0.8
    sampling_rate_hz: Optional[float] = 100.0

class SensorFingerprint(BaseModel):
    accel_mean_x: float
    accel_mean_y: float
    accel_mean_z: float
    accel_variance: float
    gyro_mean_x: float
    gyro_mean_y: float
    gyro_mean_z: float
    gyro_variance: float
    mag_mean_x: float
    mag_mean_y: float
    mag_mean_z: float
    mag_variance: float
    sensor_cross_correlation: float
    sampling_jitter_ms: float
    response_latency_ms: float
    timing_variance: float
    micro_motion_signature: float
    normalized_vector: List[float] = Field(default_factory=list)

class SensorComparisonResult(BaseModel):
    status: str  # MATCH | PARTIAL_MATCH | MISMATCH | INSUFFICIENT_DATA
    similarity_pct: float
    confidence: float
    baseline_samples_count: int
    variance_displacement: float
    provenance: str = "OBSERVED + MODEL_INFERRED"
    summary: str

class DeviceTimingAnalysis(BaseModel):
    device_time_utc: str
    backend_receive_time_utc: str
    round_trip_time_ms: float
    clock_drift_sec: float
    monotonic_delta_ms: float
    sampling_jitter_ms: float
    status: str  # NORMAL | TIMING_ANOMALY | UNAVAILABLE
    provenance: str = "OBSERVED"

class ExperimentalPUFSignal(BaseModel):
    enrollment_samples: int = 50
    intra_device_similarity: float = 0.942
    inter_device_similarity: float = 0.518
    stability_pct: float = 94.2
    estimated_entropy_bits: float = 127.4
    far_estimate_pct: float = 0.08
    frr_estimate_pct: float = 1.20
    status: str = "EXPERIMENTAL / RESEARCH SIGNAL"
    provenance: str = "EXPERIMENTAL"
    assessment: str = "SRAM power-on state evaluation indicates distinct physical entropy. Retained strictly as non-binding experimental research feature."

class DeviceTrustScore(BaseModel):
    device_id: str
    total_score: float  # 0 - 100
    trust_level: str    # TRUSTED | ELEVATED_RISK | UNTRUSTED | INSUFFICIENT_EVIDENCE
    confidence: float   # 0.0 - 1.0
    breakdown: Dict[str, float] = Field(default_factory=dict)
    unavailable_dimensions: List[str] = Field(default_factory=list)
    normalized_methodology: str
    provenance: str = "HARDWARE_ATTESTED / SYSTEM_GENERATED"
    recommendation: str

class DeviceTelemetryPacket(BaseModel):
    device_id: str
    firmware_version: str
    uptime_sec: int
    rssi_dbm: int
    battery_mv: int
    temperature_c: float
    sensor_window: SensorWindow
    timing: DeviceTimingAnalysis
    attestation_verified: bool
    puf_signal: Optional[ExperimentalPUFSignal] = None
    provenance: str = "HARDWARE_ATTESTED"

class HybridRiskInput(BaseModel):
    transaction_features: Dict[str, Any]
    behavior_features: Dict[str, Any]
    graph_features: Dict[str, Any]
    evidence_features: Dict[str, Any]
    hardware_features: Dict[str, Any]

class HybridFusionResult(BaseModel):
    classical_risk: float
    hardware_trust: float
    graph_risk: float
    evidence_risk: float
    behavior_risk: float
    quantum_signal: float
    hybrid_risk: float
    quantum_activated: bool
    activation_reason: str
    provenance: str = "SYSTEM_GENERATED"

# --------------------------------------------------------------------------
# Official Team Lead ESP32 Integration Schemas
# --------------------------------------------------------------------------

class AutoVerifyPaymentRequest(BaseModel):
    transaction_id: str = Field(..., description="Unique Transaction Identifier")
    merchant_id: str = Field("MERCHANT-ICICI-8801", description="Merchant Identifier")
    amount: float = Field(..., description="Claimed Transaction Amount")
    device_id: str = Field("QK-ESP32-7F3A", description="ESP32 Trust Node Device ID")
    timestamp_utc: str = Field(..., description="Verification Request Timestamp UTC")
    nonce: Optional[str] = Field(None, description="Cryptographic nonce from challenge")
    hmac_signature: Optional[str] = Field(None, description="Signed attestation digest from ESP32 eFuse key")
    qr_payload: Optional[str] = Field(None, description="Decoded UPI URI from QR")
    screenshot_base64: Optional[str] = Field(None, description="Optional raw base64 receipt image")
    user_id: Optional[str] = Field("USR-1001", description="Associated Payer User Identifier")

class AutoVerifyPaymentResponse(BaseModel):
    transaction_id: str
    verification_status: str  # VERIFIED | NOT_VERIFIED | REQUIRES_REVIEW
    decision: str             # APPROVE | STEP_UP | BLOCK
    risk_score: float         # 0.0 - 100.0
    trust_level: str
    led_state: str            # GREEN | AMBER | RED | RED_FLASH
    voice_alert: str          # "Payment verified." | "Additional verification required." | etc.
    mfa_level: int            # 0: Passive, 1: OTP, 2: Passkey, 3: Hardware Attestation
    mfa_action: str
    case_id: str
    evidence_match: bool
    hardware_attestation_status: str
    quantum_escalation_status: str
    latency_ms: float
    provenance: str = "HARDWARE_ATTESTED + MULTI_MODAL_VERIFIED"

class DelayedRecheckRequest(BaseModel):
    transaction_id: str
    merchant_id: str = "MERCHANT-ICICI-8801"
    device_id: str = "QK-ESP32-7F3A"
    delay_seconds: int = Field(120, description="Scheduled settlement recheck window")

class DelayedRecheckResponse(BaseModel):
    transaction_id: str
    settlement_status: str  # SETTLED | REVERSED | DISPUTED | PENDING_SETTLEMENT
    previous_status: str
    alert_triggered: bool
    alert_details: Optional[str] = None
    recheck_timestamp_utc: str
    recheck_mode: str = "SIMULATED RECHECK"
    provenance: str = "SYSTEM_GENERATED (SIMULATED RECHECK)"

class OnePressFraudReportRequest(BaseModel):
    device_id: str = "QK-ESP32-7F3A"
    last_transaction_id: str
    timestamp_utc: str
    last_risk_score: float = 0.0
    last_decision: str = "UNKNOWN"
    attestation_state: str = "VERIFIED"
    merchant_notes: Optional[str] = "Merchant one-press physical button fraud escalation"

class OnePressFraudReportResponse(BaseModel):
    case_id: str
    status: str = "INVESTIGATION_OPENED"
    device_id: str
    transaction_id: str
    timestamp_utc: str
    incident_severity: str
    recommended_actions: List[str]
    investigation_url: str
    provenance: str = "HARDWARE_ATTESTED / INCIDENT_LOGGED"

class DynamicQRRequest(BaseModel):
    merchant_id: str = "MERCHANT-ICICI-8801"
    merchant_name: str = "Verified Store Retail"
    merchant_vpa: str = "verified.store@icici"
    amount: float
    currency: str = "INR"
    expiry_seconds: int = Field(30, description="Strict TTL for dynamic QR")
    note: Optional[str] = "Invoice Dynamic QK"

class DynamicQRResponse(BaseModel):
    transaction_id: str
    merchant_id: str
    merchant_vpa: str
    amount: float
    currency: str
    nonce: str
    issued_at_utc: str
    expires_at_utc: str
    qr_payload: str
    signature_digest: str
    provenance: str = "HARDWARE_ATTESTED (DYNAMIC_QR)"

class DynamicQRVerifyRequest(BaseModel):
    qr_payload: str
    scanned_timestamp_utc: str

class DynamicQRVerifyResponse(BaseModel):
    valid: bool
    status: str  # VALID | EXPIRED | SIGNATURE_MISMATCH | MALFORMED
    transaction_id: Optional[str] = None
    merchant_id: Optional[str] = None
    amount: Optional[float] = None
    seconds_remaining: Optional[float] = None
    provenance: str = "HARDWARE_ATTESTED"

