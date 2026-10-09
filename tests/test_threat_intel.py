import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.threat_intel_service import ThreatIntelligenceService, threat_intel_service
from backend.app.core.config import settings

client = TestClient(app)

# ==============================================================================
# 1. SHA-256 & File Metadata Analysis Tests
# ==============================================================================

def test_sha256_computation_and_metadata():
    """Verify deterministic SHA-256 and magic byte detection for safe image vs binary."""
    sample_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    meta = threat_intel_service.analyze_file_metadata(sample_png, filename="receipt.png")
    assert meta["status"] == "OBSERVED"
    assert meta["detected_type"] == "IMAGE_PNG"
    assert meta["is_executable"] is False
    assert len(meta["sha256"]) == 64

    # Test PE Executable Detection
    sample_exe = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00"
    meta_exe = threat_intel_service.analyze_file_metadata(sample_exe, filename="invoice.exe")
    assert meta_exe["detected_type"] == "EXECUTABLE_PE"
    assert meta_exe["is_executable"] is True
    assert meta_exe["is_high_risk_extension"] is True

def test_known_file_hash_lookup():
    """Verify hash lookup by SHA-256 without uploading binary."""
    mock_resp_data = {
        "data": {
            "attributes": {
                "last_analysis_stats": {"malicious": 14, "suspicious": 2, "harmless": 20, "undetected": 30},
                "popular_threat_classification": {"suggested_threat_label": "Trojan.Agent"}
            }
        }
    }
    svc = ThreatIntelligenceService(api_key="test_dummy_key")
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = __import__("json").dumps(mock_resp_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = svc.lookup_file_reputation("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        assert res["status"] == "OBSERVED"
        assert res["malicious_count"] == 14
        assert res["suspicious_count"] == 2
        assert res["threat_label"] == "Trojan.Agent"
        assert res["source"] == "VIRUSTOTAL"

def test_unknown_file_hash_and_upload_disabled():
    """Unindexed file hash returns NOT_INDEXED when external upload is disabled."""
    svc = ThreatIntelligenceService(api_key="test_dummy_key")
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_err = __import__("urllib.error", fromlist=["HTTPError"]).HTTPError(
            url="http://vt.com", code=404, msg="Not Found", hdrs={}, fp=None
        )
        mock_urlopen.side_effect = mock_err

        res = svc.lookup_file_reputation("0000000000000000000000000000000000000000000000000000000000000000", allow_upload=False)
        assert res["status"] == "NOT_INDEXED"
        assert res["malicious_count"] == 0
        assert "disabled" in res["message"].lower()

# ==============================================================================
# 2. VirusTotal URL Reputation Tests
# ==============================================================================

def test_vt_unavailable_when_no_key():
    """Rule 1 & 7: API key missing returns UNAVAILABLE, never CLEAN."""
    svc = ThreatIntelligenceService(api_key="")
    res = svc.lookup_url_reputation("https://example.com")
    assert res["status"] == "UNAVAILABLE"
    assert res["source"] == "VIRUSTOTAL"
    assert res["malicious_count"] == 0

def test_vt_clean_url():
    """Verify clean URL returns vendor counts with zero malicious flags."""
    mock_resp_data = {
        "data": {
            "attributes": {
                "last_analysis_stats": {"malicious": 0, "suspicious": 0, "harmless": 78, "undetected": 10},
                "popular_threat_classification": {}
            }
        }
    }
    svc = ThreatIntelligenceService(api_key="test_key")
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = __import__("json").dumps(mock_resp_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = svc.lookup_url_reputation("https://store.hdfcbank.com")
        assert res["status"] == "OBSERVED"
        assert res["malicious_count"] == 0
        assert res["suspicious_count"] == 0
        assert res["total_vendors"] == 88

def test_vt_suspicious_url():
    """Verify suspicious URL flags generate high-severity threat signal."""
    mock_resp_data = {
        "data": {
            "attributes": {
                "last_analysis_stats": {"malicious": 1, "suspicious": 3, "harmless": 20, "undetected": 10},
                "popular_threat_classification": {"suggested_threat_label": "Suspicious"}
            }
        }
    }
    svc = ThreatIntelligenceService(api_key="test_key")
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = __import__("json").dumps(mock_resp_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = svc.lookup_url_reputation("https://suspicious-cashback.xyz")
        assert res["status"] == "OBSERVED"
        assert res["suspicious_count"] == 3

def test_vt_malicious_url_blocks():
    """Rule 4: Multi-vendor malicious flags generate CRITICAL signal and BLOCK."""
    mock_resp_data = {
        "data": {
            "attributes": {
                "last_analysis_stats": {"malicious": 12, "suspicious": 4, "harmless": 5, "undetected": 15},
                "popular_threat_classification": {"suggested_threat_label": "Phishing.Paytm"}
            }
        }
    }
    with patch("backend.app.services.threat_intel_service.ThreatIntelligenceService.lookup_url_reputation") as mock_vt:
        mock_vt.return_value = {
            "status": "OBSERVED",
            "source": "VIRUSTOTAL",
            "url": "https://fake-login-bank.xyz",
            "malicious_count": 12,
            "suspicious_count": 4,
            "harmless_count": 5,
            "total_vendors": 36,
            "threat_label": "Phishing.Paytm"
        }
        res = client.post("/api/check-payment", json={
            "input_type": "LINK",
            "payload": "https://fake-login-bank.xyz/pay"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["decision"] == "BLOCK"
        assert data["risk_score"] >= 80.0
        assert any("VirusTotal Threat Intelligence Flag" in s["name"] for s in data["risk_signals"])

# ==============================================================================
# 3. WHOIS, Domain Age, DNS, and TLS Tests
# ==============================================================================

def test_young_legitimate_domain_never_alone_malicious():
    """Rule 2: Young domain alone (<30 days) is an inferred moderate context, never auto-block."""
    with patch("backend.app.services.threat_intel_service.ThreatIntelligenceService.lookup_whois_intelligence") as mock_whois:
        mock_whois.return_value = {
            "status": "OBSERVED",
            "domain": "newly-opened-store.com",
            "registrar": "NameCheap",
            "creation_date": "2026-09-25",
            "domain_age_days": 13,
            "is_young_domain": True,
            "name_servers": ["ns1.store.com"],
            "registrant_status": "REDACTED_FOR_PRIVACY"
        }
        res = client.post("/api/check-payment", json={
            "input_type": "LINK",
            "payload": "https://newly-opened-store.com/checkout?am=500"
        })
        assert res.status_code == 200
        data = res.json()
        # Should NOT be automatically hard blocked if amount and context are benign
        assert data["decision"] in ["MONITOR", "STEP_UP", "APPROVE"]
        signal_names = [s["name"] for s in data["risk_signals"]]
        assert "Recently Registered Domain" in signal_names
        young_sig = next(s for s in data["risk_signals"] if s["name"] == "Recently Registered Domain")
        assert young_sig["severity"] == "MODERATE"

def test_invalid_url_and_ssrf():
    """Rule 11 & SSRF: Dangerous schemes and private IPs are rejected."""
    # javascript: scheme
    valid, msg, _ = threat_intel_service.normalize_and_validate_url("javascript:alert(1)")
    assert valid is False
    assert "dangerous" in msg.lower()

    # 127.0.0.1 private IP
    valid, msg, _ = threat_intel_service.normalize_and_validate_url("http://127.0.0.1:8080/admin")
    assert valid is False
    assert "ssrf" in msg.lower()

def test_unavailable_whois_and_dns():
    """Rule 1: WHOIS / DNS lookup failures are marked UNAVAILABLE without crashing."""
    res_whois = threat_intel_service.lookup_whois_intelligence("nonexistent-domain-xyz-99120.invalid")
    assert res_whois["status"] == "UNAVAILABLE"

    res_dns = threat_intel_service.inspect_dns_records("nonexistent-domain-xyz-99120.invalid")
    assert res_dns["status"] == "UNAVAILABLE"

def test_invalid_tls_and_no_false_safety():
    """Rule 3: Valid TLS alone does NOT mean safe; expired TLS triggers High RiskSignal."""
    with patch("backend.app.services.threat_intel_service.ThreatIntelligenceService.inspect_tls_certificate") as mock_tls:
        mock_tls.return_value = {
            "status": "OBSERVED",
            "domain": "expired-cert-bank.com",
            "has_tls": True,
            "issuer": "Let's Encrypt",
            "is_expired": True,
            "not_after": "Jan 01 00:00:00 2025 GMT"
        }
        res = client.post("/api/check-payment", json={
            "input_type": "LINK",
            "payload": "https://expired-cert-bank.com/pay"
        })
        assert res.status_code == 200
        data = res.json()
        assert any("Invalid TLS Certificate" in s["name"] for s in data["risk_signals"])

# ==============================================================================
# 4. Security & Privacy Constraints Tests
# ==============================================================================

def test_api_key_never_exposed_in_response():
    """Rule 6: API keys are never exposed in CheckPaymentResponse or threat intelligence."""
    res = client.post("/api/check-payment", json={
        "input_type": "LINK",
        "payload": "https://verified.store@icici.com"
    })
    assert res.status_code == 200
    text_content = res.text
    if settings.VIRUSTOTAL_API_KEY:
        assert settings.VIRUSTOTAL_API_KEY not in text_content
    if settings.GEMINI_API_KEY:
        assert settings.GEMINI_API_KEY not in text_content

def test_whois_pii_redaction():
    """Rule 14: WHOIS lookup redacts personal phone, email, and home address."""
    whois_res = threat_intel_service.lookup_whois_intelligence("google.com")
    assert "email" not in whois_res or whois_res.get("email") == "REDACTED_FOR_PRIVACY"
    assert "phone" not in whois_res or whois_res.get("phone") == "REDACTED_FOR_PRIVACY"

def test_conflicting_threat_signals_consistency():
    """Rule 12 & Single Result Guard: Conflicting signals resolve deterministically."""
    # Valid TLS + young domain + malicious VT -> Single Result Consistency Guard forces BLOCK
    with patch("backend.app.services.threat_intel_service.ThreatIntelligenceService.lookup_url_reputation") as mock_vt, \
         patch("backend.app.services.threat_intel_service.ThreatIntelligenceService.inspect_tls_certificate") as mock_tls:
        mock_vt.return_value = {
            "status": "OBSERVED",
            "source": "VIRUSTOTAL",
            "malicious_count": 8,
            "suspicious_count": 2,
            "total_vendors": 30
        }
        mock_tls.return_value = {
            "status": "OBSERVED",
            "has_tls": True,
            "issuer": "Trusted Authority",
            "is_expired": False
        }
        res = client.post("/api/check-payment", json={
            "input_type": "LINK",
            "payload": "https://fast-refund-gift.com/claim"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["decision"] == "BLOCK"
        assert "SAFE" not in data["trust_level"]
        assert data["risk_score"] >= 80.0
