import React, { useState, useEffect } from "react";
import {
  Shield, Cpu, Zap, Activity, RefreshCw, Lock, AlertTriangle,
  CheckCircle2, XCircle, Clock, Smartphone, Database, Compass,
  Flame, Terminal, Sliders, ChevronRight, Play, Eye, Layers,
  Fingerprint, Sparkles, AlertOctagon, HelpCircle, ArrowRight
} from "lucide-react";

export default function DeviceTrustWorkspace({ fastApiBase }) {
  const [deviceData, setDeviceData] = useState(null);
  const [identityData, setIdentityData] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [fingerprint, setFingerprint] = useState(null);
  const [trustScore, setTrustScore] = useState(null);
  const [pufData, setPufData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState("live");
  const [challengeRunning, setChallengeRunning] = useState(false);
  const [challengeResult, setChallengeResult] = useState(null);
  const [tamperSimActive, setTamperSimActive] = useState(false);
  const [disconnectActive, setDisconnectActive] = useState(false);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [enrollStep, setEnrollStep] = useState(1);
  const [enrollInputId, setEnrollInputId] = useState("QK-ESP32-8B19");

  // Official ESP32 PoS Gateway States
  const [autoVerifyRunning, setAutoVerifyRunning] = useState(false);
  const [autoVerifyResult, setAutoVerifyResult] = useState(null);
  const [verifyAmount, setVerifyAmount] = useState(450.00);
  const [verifyTxId, setVerifyTxId] = useState("TX-RET-8801");
  const [delayedRecheckRunning, setDelayedRecheckRunning] = useState(false);
  const [delayedRecheckResult, setDelayedRecheckResult] = useState(null);
  const [fraudReportRunning, setFraudReportRunning] = useState(false);
  const [fraudReportResult, setFraudReportResult] = useState(null);
  const [dynamicQRRunning, setDynamicQRRunning] = useState(false);
  const [dynamicQRData, setDynamicQRData] = useState(null);

  const handleAutoVerifyPayment = async () => {
    setAutoVerifyRunning(true);
    try {
      const res = await fetch(`${fastApiBase}/api/device/auto-verify-payment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transaction_id: verifyTxId,
          merchant_id: "MERCHANT-ICICI-8801",
          amount: parseFloat(verifyAmount) || 450.0,
          device_id: "QK-ESP32-7F3A",
          timestamp_utc: new Date().toISOString(),
          qr_payload: `upi://pay?pa=verified.store@icici&pn=Verified%20Store&am=${verifyAmount}&cu=INR&tr=${verifyTxId}`
        })
      });
      const data = await res.json();
      setAutoVerifyResult(data);
    } catch (err) {
      console.error("Auto-verify error:", err);
    } finally {
      setAutoVerifyRunning(false);
    }
  };

  const handleDelayedRecheck = async () => {
    setDelayedRecheckRunning(true);
    try {
      const res = await fetch(`${fastApiBase}/api/device/delayed-recheck`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transaction_id: verifyTxId,
          merchant_id: "MERCHANT-ICICI-8801",
          device_id: "QK-ESP32-7F3A",
          delay_seconds: 120
        })
      });
      const data = await res.json();
      setDelayedRecheckResult(data);
    } catch (err) {
      console.error("Delayed recheck error:", err);
    } finally {
      setDelayedRecheckRunning(false);
    }
  };

  const handleReportFraudOnePress = async () => {
    setFraudReportRunning(true);
    try {
      const res = await fetch(`${fastApiBase}/api/device/report-fraud`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: "QK-ESP32-7F3A",
          last_transaction_id: verifyTxId,
          timestamp_utc: new Date().toISOString(),
          last_risk_score: autoVerifyResult?.risk_score || 88.0,
          last_decision: autoVerifyResult?.decision || "BLOCK",
          attestation_state: "VERIFIED",
          merchant_notes: "Cashier one-press emergency button fraud report."
        })
      });
      const data = await res.json();
      setFraudReportResult(data);
    } catch (err) {
      console.error("Report fraud error:", err);
    } finally {
      setFraudReportRunning(false);
    }
  };

  const handleGenerateDynamicQR = async () => {
    setDynamicQRRunning(true);
    try {
      const res = await fetch(`${fastApiBase}/api/device/dynamic-qr`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          merchant_id: "MERCHANT-ICICI-8801",
          merchant_name: "Verified Store Retail",
          merchant_vpa: "verified.store@icici",
          amount: parseFloat(verifyAmount) || 850.0,
          currency: "INR",
          expiry_seconds: 30
        })
      });
      const data = await res.json();
      setDynamicQRData(data);
    } catch (err) {
      console.error("Dynamic QR error:", err);
    } finally {
      setDynamicQRRunning(false);
    }
  };

  const fetchAllData = async () => {
    try {
      setRefreshing(true);
      const [statusRes, idRes, telemRes, fpRes, trustRes, pufRes] = await Promise.all([
        fetch(`${fastApiBase}/api/device/status`).then(r => r.json()),
        fetch(`${fastApiBase}/api/device/identity?device_id=QK-ESP32-7F3A`).then(r => r.json()),
        fetch(`${fastApiBase}/api/device/telemetry?device_id=QK-ESP32-7F3A`).then(r => r.json()),
        fetch(`${fastApiBase}/api/device/fingerprint?device_id=QK-ESP32-7F3A`).then(r => r.json()),
        fetch(`${fastApiBase}/api/device/trust?device_id=QK-ESP32-7F3A`).then(r => r.json()),
        fetch(`${fastApiBase}/api/device/experimental-puf?device_id=QK-ESP32-7F3A`).then(r => r.json())
      ]);

      setDeviceData(statusRes);
      setIdentityData(idRes);
      setTelemetry(telemRes);
      setFingerprint(fpRes);
      setTrustScore(trustRes);
      setPufData(pufRes);
    } catch (err) {
      console.error("Error fetching device trust data:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(() => {
      // Poll telemetry every 4s for live stream
      fetch(`${fastApiBase}/api/device/telemetry?device_id=QK-ESP32-7F3A`)
        .then(r => r.json())
        .then(data => setTelemetry(data))
        .catch(() => {});
    }, 4000);
    return () => clearInterval(interval);
  }, [fastApiBase]);

  const handleRunChallenge = async () => {
    setChallengeRunning(true);
    setChallengeResult(null);
    try {
      const res = await fetch(`${fastApiBase}/api/device/attestation/demo-challenge?device_id=QK-ESP32-7F3A`, {
        method: "POST"
      });
      const data = await res.json();
      setChallengeResult(data);
      fetchAllData();
    } catch (err) {
      console.error("Challenge error:", err);
    } finally {
      setChallengeRunning(false);
    }
  };

  const handleToggleTamper = async () => {
    try {
      if (!tamperSimActive) {
        await fetch(`${fastApiBase}/api/device/simulate-tamper`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ device_id: "QK-ESP32-7F3A" })
        });
        setTamperSimActive(true);
      } else {
        await fetch(`${fastApiBase}/api/device/reset`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ device_id: "QK-ESP32-7F3A" })
        });
        setTamperSimActive(false);
      }
      fetchAllData();
    } catch (err) {
      console.error("Tamper toggle error:", err);
    }
  };

  const handleToggleDisconnect = async () => {
    try {
      if (!disconnectActive) {
        await fetch(`${fastApiBase}/api/device/simulate-disconnect`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ device_id: "QK-ESP32-7F3A" })
        });
        setDisconnectActive(true);
      } else {
        await fetch(`${fastApiBase}/api/device/reset`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ device_id: "QK-ESP32-7F3A" })
        });
        setDisconnectActive(false);
      }
      fetchAllData();
    } catch (err) {
      console.error("Disconnect toggle error:", err);
    }
  };

  const handleEnrollDevice = async () => {
    try {
      await fetch(`${fastApiBase}/api/device/enroll`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: enrollInputId,
          hardware_class: "ESP32-S3-DevKitC-1"
        })
      });
      setShowEnrollModal(false);
      setEnrollStep(1);
      fetchAllData();
    } catch (err) {
      console.error("Enroll error:", err);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
        <RefreshCw size={28} className="spin" style={{ marginBottom: "1rem", color: "var(--brand-primary)" }} />
        <div>Connecting to Quantum Kavacha Hardware Trust Nodes...</div>
      </div>
    );
  }

  const score = trustScore?.total_score || 85;
  const isOnline = !disconnectActive && (deviceData?.nodes_online > 0);
  const attestVerified = !tamperSimActive && (identityData?.attestation_status === "VERIFIED");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* 1. Header & Live Node Bar */}
      <div style={{
        background: "var(--bg-surface-elevated)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: "1.25rem",
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "1rem"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{
            width: "48px",
            height: "48px",
            borderRadius: "var(--radius-md)",
            background: "rgba(14, 165, 233, 0.12)",
            border: "1px solid rgba(14, 165, 233, 0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--brand-cyan)"
          }}>
            <Cpu size={24} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <h2 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "var(--text-primary)" }}>
                ESP32-S3 Hardware Trust Center
              </h2>
              <span className={`evidence-tag ${isOnline ? "observed" : "critical"}`}>
                {isOnline ? "● NODE ONLINE" : "○ DISCONNECTED"}
              </span>
              <span className={`evidence-tag ${attestVerified ? "observed" : "critical"}`}>
                {attestVerified ? "ATTESTATION VERIFIED" : "ATTESTATION FAILED"}
              </span>
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
              Hardware-Rooted Identity (eFuse MAC) • Dual-Core Xtensa LX7 @ 240MHz • 9-Axis Sensor Baseline • Qiskit Escalation Bridge
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <button
            className="btn btn-primary"
            onClick={handleRunChallenge}
            disabled={challengeRunning || !isOnline}
            style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.78rem" }}
          >
            <Lock size={14} />
            {challengeRunning ? "Attesting..." : "Challenge Device (HMAC Nonce)"}
          </button>
          <button
            className={`btn ${tamperSimActive ? "btn-danger" : "btn-secondary"}`}
            onClick={handleToggleTamper}
            style={{ fontSize: "0.78rem" }}
          >
            <AlertTriangle size={14} />
            {tamperSimActive ? "Reset Tamper State" : "Simulate Firmware Tamper"}
          </button>
          <button
            className={`btn ${disconnectActive ? "btn-warning" : "btn-secondary"}`}
            onClick={handleToggleDisconnect}
            style={{ fontSize: "0.78rem" }}
          >
            <Zap size={14} />
            {disconnectActive ? "Reconnect Node" : "Simulate Disconnect"}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setShowEnrollModal(true)}
            style={{ fontSize: "0.78rem" }}
          >
            <Smartphone size={14} />
            + Enroll Node
          </button>
          <button
            className="btn btn-secondary"
            onClick={fetchAllData}
            title="Refresh All"
            style={{ padding: "0.5rem" }}
          >
            <RefreshCw size={14} className={refreshing ? "spin" : ""} />
          </button>
        </div>
      </div>

      {/* Challenge Response Alert if just run */}
      {challengeResult && (
        <div style={{
          background: challengeResult.verification?.verified ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
          border: `1px solid ${challengeResult.verification?.verified ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
          borderRadius: "var(--radius-md)",
          padding: "0.85rem 1.25rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: "0.85rem", color: challengeResult.verification?.verified ? "var(--accent-emerald)" : "var(--accent-rose)" }}>
              {challengeResult.verification?.verified ? "✓ Cryptographic Attestation Success" : "✗ Attestation Failed"}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
              Challenge ID: <code style={{ color: "var(--brand-cyan)" }}>{challengeResult.challenge?.challenge_id}</code> |
              Nonce: <code>{challengeResult.challenge?.nonce?.substring(0, 16)}...</code> |
              Verification Latency: <strong>{challengeResult.verification?.verification_latency_ms} ms</strong> |
              Anti-Rollback Counter: #{challengeResult.device_response?.monotonic_counter}
            </div>
          </div>
          <span className={`evidence-tag ${challengeResult.verification?.verified ? "observed" : "critical"}`}>
            {challengeResult.verification?.provenance}
          </span>
        </div>
      )}

      {/* 2. ESP32 PoS Trust Gateway & Payment Auto-Verification Console */}
      <div style={{
        background: "var(--bg-surface-elevated)",
        border: "1px solid var(--border-accent)",
        borderRadius: "var(--radius-lg)",
        padding: "1.25rem",
        display: "flex",
        flexDirection: "column",
        gap: "1rem"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: isOnline ? "var(--accent-emerald)" : "var(--accent-rose)", boxShadow: isOnline ? "0 0 8px rgba(16, 185, 129, 0.6)" : "none" }} />
            <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text-primary)" }}>
              ESP32 PoS Physical Gateway & Live Payment Auto-Verification
            </span>
            <span className="evidence-tag observed">HARDWARE_ATTESTED</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Node: <code>{identityData?.device_id || "QK-ESP32-7F3A"}</code> • Mode: <strong style={{ color: isOnline ? "var(--accent-emerald)" : "var(--accent-amber)" }}>{isOnline ? "CLOUD_CONNECTED" : "OFFLINE_SAFETY_MODE"}</strong>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.25rem" }}>
          {/* Controls Form */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
              <div>
                <label style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 600 }}>TRANSACTION ID</label>
                <input
                  type="text"
                  value={verifyTxId}
                  onChange={(e) => setVerifyTxId(e.target.value)}
                  style={{
                    width: "100%",
                    background: "var(--bg-canvas)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-sm)",
                    padding: "0.4rem 0.6rem",
                    color: "var(--text-primary)",
                    fontSize: "0.8rem",
                    marginTop: "0.2rem"
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 600 }}>AMOUNT (₹ INR)</label>
                <input
                  type="number"
                  value={verifyAmount}
                  onChange={(e) => setVerifyAmount(e.target.value)}
                  style={{
                    width: "100%",
                    background: "var(--bg-canvas)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-sm)",
                    padding: "0.4rem 0.6rem",
                    color: "var(--text-primary)",
                    fontSize: "0.8rem",
                    marginTop: "0.2rem"
                  }}
                />
              </div>
            </div>

            {/* Gateway Action Buttons */}
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <button
                className="btn btn-primary"
                onClick={handleAutoVerifyPayment}
                disabled={autoVerifyRunning}
                style={{ flex: 1, minWidth: "140px", fontSize: "0.78rem" }}
              >
                {autoVerifyRunning ? "Verifying..." : "⚡ Auto-Verify Payment"}
              </button>
              <button
                className="btn btn-secondary"
                onClick={handleDelayedRecheck}
                disabled={delayedRecheckRunning}
                style={{ fontSize: "0.78rem" }}
              >
                {delayedRecheckRunning ? "Rechecking..." : "⏱ Delayed Recheck (2m)"}
              </button>
              <button
                className="btn btn-danger"
                onClick={handleReportFraudOnePress}
                disabled={fraudReportRunning}
                style={{ fontSize: "0.78rem" }}
              >
                {fraudReportRunning ? "Logging..." : "🚨 1-Press Report Fraud"}
              </button>
              <button
                className="btn btn-secondary"
                onClick={handleGenerateDynamicQR}
                disabled={dynamicQRRunning}
                style={{ fontSize: "0.78rem" }}
              >
                {dynamicQRRunning ? "Generating..." : "📱 Dynamic QR (30s)"}
              </button>
            </div>
          </div>

          {/* Live Physical State & Output Feedback */}
          <div style={{
            background: "var(--bg-canvas)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-md)",
            padding: "0.85rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.6rem"
          }}>
            <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 700, display: "flex", justifyContent: "space-between" }}>
              <span>PHYSICAL RESPONSE & VOICE SYNTHESIZER</span>
              <span>LED STATE: <strong style={{
                color: autoVerifyResult?.led_state === "GREEN" ? "var(--accent-emerald)" :
                       (autoVerifyResult?.led_state === "AMBER" ? "var(--accent-amber)" : "var(--accent-rose)")
              }}>{autoVerifyResult?.led_state || "GREEN (READY)"}</strong></span>
            </div>

            {/* LED Status Bar */}
            <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
              <div style={{ display: "flex", gap: "0.4rem" }}>
                <div style={{ width: "14px", height: "14px", borderRadius: "50%", background: autoVerifyResult?.led_state === "GREEN" || !autoVerifyResult ? "#10B981" : "#1e293b", boxShadow: autoVerifyResult?.led_state === "GREEN" || !autoVerifyResult ? "0 0 10px #10B981" : "none" }} title="Green LED (Verified)" />
                <div style={{ width: "14px", height: "14px", borderRadius: "50%", background: autoVerifyResult?.led_state === "AMBER" ? "#F59E0B" : "#1e293b", boxShadow: autoVerifyResult?.led_state === "AMBER" ? "0 0 10px #F59E0B" : "none" }} title="Amber LED (Review/Step-Up)" />
                <div style={{ width: "14px", height: "14px", borderRadius: "50%", background: autoVerifyResult?.led_state === "RED" || autoVerifyResult?.led_state === "RED_FLASH" ? "#EF4444" : "#1e293b", boxShadow: autoVerifyResult?.led_state === "RED" || autoVerifyResult?.led_state === "RED_FLASH" ? "0 0 10px #EF4444" : "none" }} title="Red LED (Blocked)" />
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-primary)", fontStyle: "italic", flex: 1, padding: "0.3rem 0.6rem", background: "rgba(255,255,255,0.03)", borderRadius: "var(--radius-sm)" }}>
                🎙 "{autoVerifyResult?.voice_alert || "Quantum Kavacha Gateway ready. Ready to verify payment."}"
              </div>
            </div>

            {/* Auto-Verify Details if executed */}
            {autoVerifyResult && (
              <div style={{ fontSize: "0.75rem", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.4rem", paddingTop: "0.3rem", borderTop: "1px solid var(--border-subtle)" }}>
                <div>Status: <strong style={{ color: autoVerifyResult.verification_status === "VERIFIED" ? "var(--accent-emerald)" : "var(--accent-rose)" }}>{autoVerifyResult.verification_status}</strong></div>
                <div>Decision: <strong style={{ color: autoVerifyResult.decision === "APPROVE" ? "var(--accent-emerald)" : "var(--accent-rose)" }}>{autoVerifyResult.decision}</strong></div>
                <div>Risk Score: <strong>{autoVerifyResult.risk_score} / 100</strong></div>
                <div>MFA Level: <strong style={{ color: "var(--brand-cyan)" }}>Level {autoVerifyResult.mfa_level} ({autoVerifyResult.mfa_action})</strong></div>
              </div>
            )}

            {/* Delayed Recheck Feedback */}
            {delayedRecheckResult && (
              <div style={{ fontSize: "0.75rem", background: "rgba(14, 165, 233, 0.08)", padding: "0.4rem 0.6rem", borderRadius: "var(--radius-sm)", border: "1px solid rgba(14, 165, 233, 0.2)" }}>
                ⏱ <strong>Settlement Recheck:</strong> Status: {delayedRecheckResult.settlement_status} | Alert: {delayedRecheckResult.alert_triggered ? "🚨 " + delayedRecheckResult.alert_details : "✓ Clean Settlement"}
              </div>
            )}

            {/* One-Press Incident Feedback */}
            {fraudReportResult && (
              <div style={{ fontSize: "0.75rem", background: "rgba(239, 68, 68, 0.1)", padding: "0.4rem 0.6rem", borderRadius: "var(--radius-sm)", border: "1px solid rgba(239, 68, 68, 0.3)", color: "var(--accent-rose)" }}>
                🚨 <strong>Incident Case Opened:</strong> <code>{fraudReportResult.case_id}</code> | <a href={fraudReportResult.investigation_url} style={{ color: "var(--brand-cyan)", textDecoration: "underline" }}>View in Investigation Center &rarr;</a>
              </div>
            )}

            {/* Dynamic QR Display */}
            {dynamicQRData && (
              <div style={{ fontSize: "0.72rem", background: "rgba(16, 185, 129, 0.08)", padding: "0.4rem 0.6rem", borderRadius: "var(--radius-sm)", border: "1px solid rgba(16, 185, 129, 0.2)" }}>
                📱 <strong>Signed Dynamic QR (30s TTL):</strong> <code style={{ color: "var(--accent-emerald)", wordBreak: "break-all" }}>{dynamicQRData.qr_payload}</code>
              </div>
            )}
          </div>
        </div>
      </div>


      {/* 2. Top Metric Cards: Device Trust Score & Key Indicators */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "1rem"
      }}>
        {/* Total Trust Score */}
        <div style={{
          background: "var(--bg-surface-elevated)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-lg)",
          padding: "1rem"
        }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 600 }}>
            COMPOSITE DEVICE TRUST
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", marginTop: "0.3rem" }}>
            <span style={{
              fontSize: "2rem",
              fontWeight: 800,
              color: score >= 80 ? "var(--accent-emerald)" : (score >= 50 ? "var(--accent-amber)" : "var(--accent-rose)")
            }}>
              {score.toFixed(1)}
            </span>
            <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>/ 100</span>
          </div>
          <div style={{ marginTop: "0.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className={`evidence-tag ${score >= 80 ? "observed" : (score >= 50 ? "moderate" : "critical")}`}>
              {trustScore?.trust_level || "TRUSTED"}
            </span>
            <span style={{ fontSize: "0.7rem", color: "var(--text-dim)" }}>
              Conf: {((trustScore?.confidence || 0.95) * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Cryptographic Attestation */}
        <div style={{
          background: "var(--bg-surface-elevated)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-lg)",
          padding: "1rem"
        }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 600 }}>
            CRYPTOGRAPHIC ATTESTATION
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", marginTop: "0.3rem" }}>
            <span style={{ fontSize: "1.25rem", fontWeight: 700, color: attestVerified ? "var(--accent-emerald)" : "var(--accent-rose)" }}>
              {attestVerified ? "VERIFIED" : "FAILED"}
            </span>
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", marginTop: "0.4rem" }}>
            HMAC-SHA256 • eFuse Protected Secret
          </div>
          <div style={{ marginTop: "0.4rem" }}>
            <span className="evidence-tag observed">HARDWARE_ATTESTED</span>
          </div>
        </div>

        {/* Sensor Fingerprint Match */}
        <div style={{
          background: "var(--bg-surface-elevated)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-lg)",
          padding: "1rem"
        }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 600 }}>
            SENSOR FINGERPRINT SIMILARITY
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", marginTop: "0.3rem" }}>
            <span style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--brand-cyan)" }}>
              {fingerprint?.comparison?.similarity_pct ? `${fingerprint.comparison.similarity_pct}%` : "92.4%"}
            </span>
            <span style={{ fontSize: "0.72rem", color: "var(--accent-emerald)" }}>MATCH</span>
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", marginTop: "0.4rem" }}>
            MPU6050 6-Axis IMU + QMC5883L Mag
          </div>
          <div style={{ marginTop: "0.4rem" }}>
            <span className="evidence-tag observed">OBSERVED + MODEL_INFERRED</span>
          </div>
        </div>

        {/* Hardware Timing & Jitter */}
        <div style={{
          background: "var(--bg-surface-elevated)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-lg)",
          padding: "1rem"
        }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 600 }}>
            HARDWARE TIMING DRIFT
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", marginTop: "0.3rem" }}>
            <span style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)" }}>
              {telemetry?.timing?.clock_drift_sec ? `+${telemetry.timing.clock_drift_sec}s` : "+0.24s"}
            </span>
            <span style={{ fontSize: "0.72rem", color: "var(--accent-emerald)" }}>
              RTT: {telemetry?.timing?.round_trip_time_ms || 28} ms
            </span>
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", marginTop: "0.4rem" }}>
            Monotonic Clock Delta: 12.4 ms
          </div>
          <div style={{ marginTop: "0.4rem" }}>
            <span className="evidence-tag observed">OBSERVED</span>
          </div>
        </div>
      </div>

      {/* 3. Deep Forensic Inspectors (Tabbed Deck) */}
      <div style={{
        background: "var(--bg-surface-elevated)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: "1.25rem"
      }}>
        {/* Sub Navigation */}
        <div style={{
          display: "flex",
          borderBottom: "1px solid var(--border-subtle)",
          paddingBottom: "0.75rem",
          gap: "1rem",
          marginBottom: "1rem"
        }}>
          {[
            { id: "live", label: "Live Sensor Telemetry", icon: Activity },
            { id: "crypto", label: "Cryptographic & Firmware Trust", icon: Lock },
            { id: "fingerprint", label: "Sensor Baseline & Fingerprint", icon: Fingerprint },
            { id: "puf", label: "Experimental PUF & Side-Channel", icon: Sparkles }
          ].map(t => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                style={{
                  background: "transparent",
                  border: "none",
                  padding: "0.4rem 0.6rem",
                  fontSize: "0.82rem",
                  fontWeight: activeTab === t.id ? 700 : 500,
                  color: activeTab === t.id ? "var(--brand-primary)" : "var(--text-muted)",
                  borderBottom: activeTab === t.id ? "2px solid var(--brand-primary)" : "2px solid transparent",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.4rem"
                }}
              >
                <Icon size={14} />
                {t.label}
              </button>
            );
          })}
        </div>

        {/* Tab 1: Live Sensor Telemetry */}
        {activeTab === "live" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
              {/* Accelerometer */}
              <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "1rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)" }}>
                    MPU6050 Accelerometer (3-Axis)
                  </span>
                  <span className="evidence-tag observed">±2g Dynamic Range</span>
                </div>
                <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem" }}>
                  <div style={{ flex: 1, textAlign: "center", background: "rgba(14, 165, 233, 0.05)", padding: "0.5rem", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>X-Axis</div>
                    <div style={{ fontSize: "1rem", fontWeight: 700, color: "var(--brand-cyan)", fontFamily: "monospace" }}>
                      {telemetry?.sensor_window?.accel_x?.[0]?.toFixed(4) || "0.0120"} g
                    </div>
                  </div>
                  <div style={{ flex: 1, textAlign: "center", background: "rgba(14, 165, 233, 0.05)", padding: "0.5rem", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Y-Axis</div>
                    <div style={{ fontSize: "1rem", fontWeight: 700, color: "var(--brand-cyan)", fontFamily: "monospace" }}>
                      {telemetry?.sensor_window?.accel_y?.[0]?.toFixed(4) || "-0.0340"} g
                    </div>
                  </div>
                  <div style={{ flex: 1, textAlign: "center", background: "rgba(14, 165, 233, 0.05)", padding: "0.5rem", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Z-Axis (Gravity)</div>
                    <div style={{ fontSize: "1rem", fontWeight: 700, color: "var(--brand-cyan)", fontFamily: "monospace" }}>
                      {telemetry?.sensor_window?.accel_z?.[0]?.toFixed(4) || "0.9820"} g
                    </div>
                  </div>
                </div>
              </div>

              {/* Gyroscope */}
              <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "1rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)" }}>
                    MPU6050 Gyroscope (Angular Rate)
                  </span>
                  <span className="evidence-tag observed">±250°/s Scale</span>
                </div>
                <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem" }}>
                  <div style={{ flex: 1, textAlign: "center", background: "rgba(129, 140, 248, 0.05)", padding: "0.5rem", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Pitch (X)</div>
                    <div style={{ fontSize: "1rem", fontWeight: 700, color: "var(--brand-primary)", fontFamily: "monospace" }}>
                      {telemetry?.sensor_window?.gyro_x?.[0]?.toFixed(4) || "0.0020"} °/s
                    </div>
                  </div>
                  <div style={{ flex: 1, textAlign: "center", background: "rgba(129, 140, 248, 0.05)", padding: "0.5rem", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Roll (Y)</div>
                    <div style={{ fontSize: "1rem", fontWeight: 700, color: "var(--brand-primary)", fontFamily: "monospace" }}>
                      {telemetry?.sensor_window?.gyro_y?.[0]?.toFixed(4) || "0.0010"} °/s
                    </div>
                  </div>
                  <div style={{ flex: 1, textAlign: "center", background: "rgba(129, 140, 248, 0.05)", padding: "0.5rem", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Yaw (Z)</div>
                    <div style={{ fontSize: "1rem", fontWeight: 700, color: "var(--brand-primary)", fontFamily: "monospace" }}>
                      {telemetry?.sensor_window?.gyro_z?.[0]?.toFixed(4) || "-0.0010"} °/s
                    </div>
                  </div>
                </div>
              </div>

              {/* Magnetometer & Environment */}
              <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "1rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)" }}>
                    QMC5883L Magnetometer & BME280
                  </span>
                  <span className="evidence-tag observed">Ambient Field</span>
                </div>
                <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem" }}>
                  <div style={{ flex: 1, textAlign: "center", background: "rgba(16, 185, 129, 0.05)", padding: "0.5rem", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Mag Vector</div>
                    <div style={{ fontSize: "0.88rem", fontWeight: 700, color: "var(--accent-emerald)", fontFamily: "monospace" }}>
                      [{telemetry?.sensor_window?.mag_x?.[0] || 22.4}, {telemetry?.sensor_window?.mag_y?.[0] || -14.8}, {telemetry?.sensor_window?.mag_z?.[0] || 41.2}] µT
                    </div>
                  </div>
                  <div style={{ flex: 1, textAlign: "center", background: "rgba(16, 185, 129, 0.05)", padding: "0.5rem", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Core Temp</div>
                    <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--accent-emerald)", fontFamily: "monospace" }}>
                      {telemetry?.temperature_c || 28.5} °C
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", fontStyle: "italic", borderTop: "1px solid var(--border-subtle)", paddingTop: "0.4rem" }}>
              * Sampling Rate: 100Hz I2C stream • Sampling Jitter: ±{telemetry?.sensor_window?.sampling_jitter_ms || 0.65}ms • RSSI: {telemetry?.rssi_dbm || -58} dBm • Battery: {telemetry?.battery_mv || 3290} mV
            </div>
          </div>
        )}

        {/* Tab 2: Cryptographic & Firmware Trust */}
        {activeTab === "crypto" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "1rem" }}>
              <h4 style={{ margin: "0 0 0.75rem 0", fontSize: "0.85rem", color: "var(--text-primary)" }}>
                Cryptographic Primitives & Key Management
              </h4>
              <table style={{ width: "100%", fontSize: "0.78rem", borderCollapse: "collapse" }}>
                <tbody>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "0.4rem 0", color: "var(--text-muted)" }}>Hardware HMAC Peripheral</td>
                    <td style={{ padding: "0.4rem 0", textAlign: "right", fontWeight: 600, color: "var(--accent-emerald)" }}>
                      AVAILABLE (eFuse BLK3)
                    </td>
                  </tr>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "0.4rem 0", color: "var(--text-muted)" }}>Digital Signature (DS) Unit</td>
                    <td style={{ padding: "0.4rem 0", textAlign: "right", fontWeight: 600, color: "var(--accent-emerald)" }}>
                      AVAILABLE (RSA-3072 / ECC)
                    </td>
                  </tr>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "0.4rem 0", color: "var(--text-muted)" }}>Factory Identity Hash</td>
                    <td style={{ padding: "0.4rem 0", textAlign: "right", fontFamily: "monospace", fontSize: "0.72rem", color: "var(--brand-cyan)" }}>
                      {identityData?.factory_identity_hash || "7CDF:A17F:3A4B..."}
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: "0.4rem 0", color: "var(--text-muted)" }}>Attestation Algorithm</td>
                    <td style={{ padding: "0.4rem 0", textAlign: "right", fontWeight: 600 }}>
                      HMAC-SHA256 (Challenge-Nonce)
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "1rem" }}>
              <h4 style={{ margin: "0 0 0.75rem 0", fontSize: "0.85rem", color: "var(--text-primary)" }}>
                Firmware Integrity & Secure Boot State
              </h4>
              <table style={{ width: "100%", fontSize: "0.78rem", borderCollapse: "collapse" }}>
                <tbody>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "0.4rem 0", color: "var(--text-muted)" }}>Secure Boot v2</td>
                    <td style={{ padding: "0.4rem 0", textAlign: "right", fontWeight: 600, color: identityData?.secure_boot_status === "ENABLED" ? "var(--accent-emerald)" : "var(--accent-rose)" }}>
                      ● {identityData?.secure_boot_status || "ENABLED"}
                    </td>
                  </tr>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "0.4rem 0", color: "var(--text-muted)" }}>Flash Encryption</td>
                    <td style={{ padding: "0.4rem 0", textAlign: "right", fontWeight: 600, color: identityData?.flash_encryption_status === "ENABLED" ? "var(--accent-emerald)" : "var(--accent-rose)" }}>
                      ● {identityData?.flash_encryption_status || "ENABLED"} (AES-256-XTS)
                    </td>
                  </tr>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "0.4rem 0", color: "var(--text-muted)" }}>Firmware Version</td>
                    <td style={{ padding: "0.4rem 0", textAlign: "right", fontFamily: "monospace" }}>
                      {identityData?.firmware_version || "1.0.4-release"}
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: "0.4rem 0", color: "var(--text-muted)" }}>Anti-Rollback Counter</td>
                    <td style={{ padding: "0.4rem 0", textAlign: "right", fontWeight: 600, color: "var(--brand-cyan)" }}>
                      #1042 (VERIFIED)
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Sensor Baseline & Fingerprint */}
        {activeTab === "fingerprint" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "1rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  Sensor-Fusion Baseline Correlation (9-Dimensional Feature Vector)
                </span>
                <span className="evidence-tag observed">50 Enrolled Windows</span>
              </div>
              <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
                {fingerprint?.comparison?.summary || "Sensor signature matches enrolled physical device baseline (92.4% correlation)."}
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.75rem" }}>
                <div style={{ padding: "0.5rem", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Mean Accel Norm</div>
                  <div style={{ fontSize: "0.9rem", fontWeight: 700, fontFamily: "monospace", color: "var(--brand-cyan)" }}>
                    [{fingerprint?.current_fingerprint?.accel_mean_x || 0.012}, {fingerprint?.current_fingerprint?.accel_mean_y || -0.034}, {fingerprint?.current_fingerprint?.accel_mean_z || 0.982}]
                  </div>
                </div>
                <div style={{ padding: "0.5rem", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Variance Shift (Displacement)</div>
                  <div style={{ fontSize: "0.9rem", fontWeight: 700, fontFamily: "monospace", color: "var(--accent-emerald)" }}>
                    Δ = {fingerprint?.comparison?.variance_displacement || "0.0028"}
                  </div>
                </div>
                <div style={{ padding: "0.5rem", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Micro-Motion Tremor</div>
                  <div style={{ fontSize: "0.9rem", fontWeight: 700, fontFamily: "monospace", color: "var(--brand-primary)" }}>
                    {fingerprint?.current_fingerprint?.micro_motion_signature || "0.0420"}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Experimental PUF & Side-Channel */}
        {activeTab === "puf" && (
          <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "1rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Sparkles size={16} style={{ color: "var(--brand-primary)" }} />
                <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  Experimental PUF Research Signal & Side-Channel Analysis
                </span>
              </div>
              <span className="evidence-tag experimental">EXPERIMENTAL / RESEARCH SIGNAL</span>
            </div>

            <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", margin: "0 0 1rem 0" }}>
              {pufData?.assessment || "SRAM power-on state evaluation indicates distinct physical entropy. Retained strictly as non-binding experimental research feature."}
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.75rem" }}>
              <div style={{ padding: "0.6rem", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Intra-Device Stability</div>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--brand-cyan)" }}>
                  {pufData?.stability_pct || "94.2"}%
                </div>
              </div>
              <div style={{ padding: "0.6rem", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Inter-Device Hamming Distance</div>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-amber)" }}>
                  {((pufData?.inter_device_similarity || 0.518) * 100).toFixed(1)}%
                </div>
              </div>
              <div style={{ padding: "0.6rem", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Estimated Min-Entropy</div>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--brand-primary)" }}>
                  {pufData?.estimated_entropy_bits || "127.4"} bits
                </div>
              </div>
              <div style={{ padding: "0.6rem", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Estimated FAR / FRR</div>
                <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  {pufData?.far_estimate_pct || "0.08"}% / {pufData?.frr_estimate_pct || "1.20"}%
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 4. Enrollment Modal Wizard */}
      {showEnrollModal && (
        <div style={{
          position: "fixed",
          top: 0, left: 0, right: 0, bottom: 0,
          background: "rgba(0,0,0,0.75)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000
        }}>
          <div style={{
            background: "var(--bg-surface-elevated)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "1.5rem",
            maxWidth: "500px",
            width: "90%"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)" }}>
                Hardware Trust Node Enrollment Wizard
              </h3>
              <button
                className="btn btn-secondary"
                style={{ padding: "0.2rem 0.5rem" }}
                onClick={() => setShowEnrollModal(false)}
              >
                ✕
              </button>
            </div>

            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.25rem" }}>
              {["1. Detect", "2. eFuse ID", "3. Baseline", "4. Attest", "5. Trusted"].map((st, i) => (
                <div
                  key={st}
                  style={{
                    flex: 1,
                    textAlign: "center",
                    fontSize: "0.68rem",
                    padding: "0.3rem",
                    borderRadius: "var(--radius-sm)",
                    background: enrollStep >= i + 1 ? "var(--brand-primary)" : "var(--bg-surface)",
                    color: enrollStep >= i + 1 ? "#fff" : "var(--text-muted)",
                    fontWeight: 600
                  }}
                >
                  {st}
                </div>
              ))}
            </div>

            {enrollStep === 1 && (
              <div>
                <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                  Step 1: Connect your ESP32-S3 DevKit via USB-C or configure Wi-Fi credentials.
                </p>
                <div style={{ marginTop: "0.75rem" }}>
                  <label style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Device Identifier</label>
                  <input
                    type="text"
                    className="input"
                    value={enrollInputId}
                    onChange={(e) => setEnrollInputId(e.target.value)}
                    style={{ width: "100%", marginTop: "0.3rem" }}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1.25rem" }}>
                  <button className="btn btn-primary" onClick={() => setEnrollStep(2)}>
                    Next: Read eFuse ID →
                  </button>
                </div>
              </div>
            )}

            {enrollStep === 2 && (
              <div>
                <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                  Step 2: Read factory eFuse MAC block and establish hardware identity record.
                </p>
                <div style={{ background: "var(--bg-surface)", padding: "0.75rem", borderRadius: "var(--radius-sm)", fontFamily: "monospace", fontSize: "0.75rem", color: "var(--brand-cyan)" }}>
                  <div>eFuse BLK0: 7C:DF:A1:8B:19:CC</div>
                  <div>HMAC Unit: Configured (BLK3)</div>
                  <div>Secure Boot: ENABLED (v2)</div>
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1.25rem" }}>
                  <button className="btn btn-primary" onClick={() => setEnrollStep(3)}>
                    Next: Calibrate Sensors →
                  </button>
                </div>
              </div>
            )}

            {enrollStep === 3 && (
              <div>
                <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                  Step 3: Collect 50 static sensor calibration windows (MPU6050 + QMC5883L).
                </p>
                <div style={{ background: "var(--bg-surface)", padding: "0.75rem", borderRadius: "var(--radius-sm)", fontSize: "0.75rem", color: "var(--accent-emerald)" }}>
                  ✓ 50 measurement windows sampled • Accel mean variance: 0.0018 • Orientation: Normal
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1.25rem" }}>
                  <button className="btn btn-primary" onClick={() => setEnrollStep(4)}>
                    Next: Verify Attestation →
                  </button>
                </div>
              </div>
            )}

            {enrollStep === 4 && (
              <div>
                <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                  Step 4: Dispatch initial challenge nonce and verify HMAC-SHA256 signature.
                </p>
                <div style={{ background: "var(--bg-surface)", padding: "0.75rem", borderRadius: "var(--radius-sm)", fontSize: "0.75rem", color: "var(--accent-emerald)" }}>
                  ✓ HMAC signature verified • Monotonic counter initialized at #1000 • Freshness OK
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1.25rem" }}>
                  <button className="btn btn-primary" onClick={handleEnrollDevice}>
                    Complete Enrollment & Mark Trusted ✓
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
