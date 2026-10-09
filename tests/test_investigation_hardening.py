import pytest
import time
import base64
import hashlib
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.investigation_service import investigation_service
from backend.app.services.threat_intel_service import threat_intel_service
from backend.app.services.payment_forensics import payment_forensics_service
from backend.app.db.database import get_db_connection

client = TestClient(app)

def test_direct_case_creation_and_audit_verification():
    """Verify direct unified investigation case creation and SHA-256 audit chain integrity."""
    payload = {
        "title": "Suspicious Merchant Phishing QR",
        "input_type": "QR",
        "payload": "upi://pay?pa=malicious.mule@ybl&pn=Fake%20Support&am=45000.00&cu=INR&tn=Immediate%20KYC%20verification%20fee",
        "transaction_context": {
            "amount": 45000.0,
            "device_score": 0.85,
            "location_score": 0.70,
            "recipient_vpa": "malicious.mule@ybl"
        },
        "analyst_note": "Initial intake note from automated ingest pipeline."
    }

    resp = client.post("/api/investigation/cases", json=payload)
    assert resp.status_code == 200, resp.text
    case_data = resp.json()
    case_id = case_data["case_id"]
    assert case_id.startswith("QF-")
    assert case_data["risk"]["risk_score"] > 0.0

    # Verify audit chain endpoint
    audit_resp = client.get(f"/api/investigation/cases/{case_id}/audit-verify")
    assert audit_resp.status_code == 200, audit_resp.text
    audit_res = audit_resp.json()
    assert audit_res["is_valid"] is True
    assert audit_res["integrity_status"] == "CRYPTOGRAPHICALLY_VERIFIED"
    assert audit_res["total_entries"] >= 2
    assert len(audit_res["root_hash"]) == 64

def test_audit_chain_tamper_detection():
    """Verify that tampering with an audit chain entry is detected cryptographically."""
    # Create a fresh case
    payload = {
        "title": "Tamper Test Case",
        "input_type": "LINK",
        "payload": "https://secure-hdfc-rewards.xyz/login",
    }
    resp = client.post("/api/investigation/cases", json=payload)
    assert resp.status_code == 200
    case_id = resp.json()["case_id"]

    # Retrieve from DB and maliciously modify an audit entry
    case_obj = investigation_service.get_case(case_id)
    assert case_obj is not None
    assert len(case_obj.audit_chain) > 0

    # Tamper with the details of the first entry without updating entry_hash
    case_obj.audit_chain[0]["details"] = "MALICIOUSLY TAMPERED DETAILS"
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE investigation_cases SET case_data = ? WHERE case_id = ?",
            (case_obj.model_dump_json(), case_id)
        )
        conn.commit()

    # Verify audit check catches the tamper
    verify_res = investigation_service.verify_case_audit_chain(case_id)
    assert verify_res["is_valid"] is False
    assert verify_res["integrity_status"] == "TAMPER_DETECTED"
    assert len(verify_res["errors"]) > 0

def test_case_reanalysis_and_augmentation():
    """Verify re-analysis endpoint augments case without duplicating records."""
    # Seed or fetch default case
    case_id = "QF-20261007-49910"
    re_req = {
        "re_run_all": False,
        "additional_transaction_context": {
            "supplementary_device_id": "DEV-HARDENED-SECURE",
            "mfa_verified": "true"
        }
    }
    resp = client.post(f"/api/investigation/cases/{case_id}/analyze", json=re_req)
    assert resp.status_code == 200, resp.text
    updated = resp.json()
    assert updated["case_id"] == case_id

    # Verify audit chain reflects re-analysis
    verify_resp = client.get(f"/api/investigation/cases/{case_id}/audit-verify")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["is_valid"] is True

def test_case_reset_endpoint():
    """Verify that POST /api/investigation/reset restores clean evaluation fixtures."""
    resp = client.post("/api/investigation/reset")
    assert resp.status_code == 200, resp.text
    res = resp.json()
    assert res["status"] == "RESET_SUCCESSFUL"
    assert res["active_cases"] >= 1

def test_punycode_homograph_and_credential_detection():
    """Verify detection of Punycode homographs and embedded credentials."""
    # 1. Embedded credentials test
    cred_url = "https://admin:secret123@legitbank.com/transfer"
    is_safe, msg, meta = threat_intel_service.normalize_and_validate_url(cred_url)
    assert is_safe is False
    assert meta["has_embedded_credentials"] is True
    assert "embedded credentials" in msg.lower()

    # 2. Punycode detection test
    puny_url = "https://xn--sbi-8ka.com/login"
    is_safe_puny, msg_puny, meta_puny = threat_intel_service.normalize_and_validate_url(puny_url)
    assert meta_puny["has_punycode"] is True
    assert meta_puny["punycode_decoded"] is not None

    # 3. Path traversal test
    traversal_url = "https://bank.com/portal/../../etc/passwd"
    is_safe_t, msg_t, meta_t = threat_intel_service.normalize_and_validate_url(traversal_url)
    assert is_safe_t is False
    assert meta_t["has_path_traversal"] is True

def test_qr_plain_text_vs_url_classification():
    """Verify that plain text QR codes are not falsely flagged as invalid URL schemes."""
    plain_qr = "Customer Support: 1800-123-4567, Desk Bangalore"
    req = {
        "input_type": "QR",
        "payload": plain_qr
    }
    resp = client.post("/api/check-payment", json=req)
    assert resp.status_code == 200
    res = resp.json()
    # Should not have 'Unsafe QR Destination' critical signal
    signal_names = [s["name"] for s in res.get("risk_signals", [])]
    assert "Unsafe QR Destination" not in signal_names

def test_file_guardian_magic_bytes_and_executable_rejection():
    """Verify magic bytes validation and PE/ELF rejection."""
    # Fake PE Executable (MZ header)
    pe_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"
    meta = threat_intel_service.analyze_file_metadata(pe_bytes, filename="payment_slip.exe")
    assert meta["is_executable"] is True
    assert meta["detected_type"] == "EXECUTABLE_PE"
    assert meta["is_high_risk_extension"] is True

    # Genuine PNG header
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    meta_png = threat_intel_service.analyze_file_metadata(png_bytes, filename="receipt.png")
    assert meta_png["is_executable"] is False
    assert meta_png["detected_type"] == "IMAGE_PNG"
    assert len(meta_png["sha256"]) == 64
