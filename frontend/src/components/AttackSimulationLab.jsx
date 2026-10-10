import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  QrCode,
  Download,
  Play,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  RefreshCw,
  Cpu,
  ShieldAlert,
  ArrowRight,
  Sliders,
  ExternalLink,
  Layers,
  Terminal,
  Activity
} from "lucide-react";

export function AttackSimulationLab({ fastApiBase = "", onSendToDetection }) {
  const [scenarioType, setScenarioType] = useState("PHISHING_PAYMENT_LURE");
  const [customTxn, setCustomTxn] = useState("");
  const [generating, setGenerating] = useState(false);
  const [qrArtifact, setQrArtifact] = useState(null);
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const apiBase = fastApiBase ? fastApiBase.replace(/\/+$/, "") : "";

  // Auto-generate initial QR artifact on mount
  useEffect(() => {
    generateSimulatedQR("PHISHING_PAYMENT_LURE");
  }, []);

  const generateSimulatedQR = async (selectedType = scenarioType) => {
    setGenerating(true);
    setErrorMsg(null);
    setEvalResult(null);
    try {
      const url = `${apiBase}/api/attack-lab/generate-qr`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_type: selectedType,
          custom_txn: customTxn.trim() || undefined
        })
      });
      if (!res.ok) {
        throw new Error(`Failed to generate simulated QR (HTTP ${res.status})`);
      }
      const data = await res.json();
      setQrArtifact(data);
    } catch (err) {
      console.error("QR Generation Error:", err);
      setErrorMsg(err.message || "Failed to generate simulated QR");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadPNG = () => {
    if (!qrArtifact?.qr_data_uri) return;
    const link = document.createElement("a");
    link.href = qrArtifact.qr_data_uri;
    link.download = qrArtifact.file_name || "simulated_attack_qr.png";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleRunEvaluation = async () => {
    if (!qrArtifact?.qr_base64 && !qrArtifact?.decoded_payload) return;
    setEvaluating(true);
    setErrorMsg(null);
    try {
      // Submit actual QR PNG image bytes through the image-analysis path
      const url = `${apiBase}/api/check-payment`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          input_type: "QR",
          payload: "",
          image_base64: qrArtifact.qr_base64 || undefined,
          allow_external_threat_lookup: false
        })
      });
      if (!res.ok) {
        throw new Error(`Detection pipeline error (HTTP ${res.status})`);
      }
      const data = await res.json();
      setEvalResult(data);
    } catch (err) {
      console.error("Evaluation Error:", err);
      setErrorMsg(err.message || "Failed to evaluate simulated payload");
    } finally {
      setEvaluating(false);
    }
  };

  // Determine comparison evaluation verdict
  const getComparisonVerdict = () => {
    if (!evalResult) return null;
    const expected = qrArtifact?.ground_truth_label || "SIMULATED_SUSPICIOUS";
    const decision = evalResult.decision; // BLOCK, STEP_UP, MONITOR, APPROVE
    const riskScore = evalResult.risk_score;

    if (expected === "SIMULATED_BENIGN") {
      if (decision === "APPROVE" || riskScore <= 35) {
        return {
          status: "SUCCESS",
          badge: "DETECTED CORRECTLY (BENIGN)",
          color: "var(--color-safe)",
          icon: <CheckCircle2 size={16} />,
          summary: "The detection engine correctly validated this clean transaction as safe without raising a false positive."
        };
      } else {
        return {
          status: "MISSED",
          badge: "FALSE POSITIVE",
          color: "var(--color-high-risk)",
          icon: <XCircle size={16} />,
          summary: "The engine flagged or blocked a benign retail QR transaction."
        };
      }
    }

    if (expected === "SIMULATED_SUSPICIOUS") {
      if (decision === "BLOCK" || decision === "STEP_UP" || riskScore >= 50) {
        return {
          status: "SUCCESS",
          badge: "DETECTED CORRECTLY",
          color: "var(--color-safe)",
          icon: <CheckCircle2 size={16} />,
          summary: "The detection engine correctly classified this simulated attack artifact as dangerous / step-up intervention required."
        };
      } else {
        return {
          status: "MISSED",
          badge: "DETECTION MISSED",
          color: "var(--color-high-risk)",
          icon: <XCircle size={16} />,
          summary: "The engine approved or under-scored the simulated threat."
        };
      }
    }

    return {
      status: "INCONCLUSIVE",
      badge: "INCONCLUSIVE",
      color: "var(--color-caution)",
      icon: <HelpCircle size={16} />,
      summary: "Comparison completed with borderline confidence."
    };
  };

  const compVerdict = getComparisonVerdict();

  return (
    <div className="attack-sim-lab" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* 1. Header Banner with Simulation Mode Disclosures */}
      <div
        className="glass-panel"
        style={{
          borderLeft: "4px solid var(--brand-cyan)",
          background: "linear-gradient(135deg, rgba(14, 165, 233, 0.08) 0%, rgba(9, 13, 22, 0.7) 100%)",
          padding: "1.25rem 1.5rem"
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.25rem" }}>
              <Terminal size={22} style={{ color: "var(--brand-cyan)" }} />
              <h2 style={{ margin: 0, fontSize: "1.25rem", color: "var(--text-primary)", fontWeight: 700 }}>
                Attack Simulation Lab & Controlled Adversarial Testbed
              </h2>
            </div>
            <p style={{ margin: 0, fontSize: "0.84rem", color: "var(--text-secondary)", maxWidth: "800px" }}>
              Generate verifiable, high-contrast QR PNG artifacts using standard RFC 2606/6761 compliant test domains. Inspect decoded payloads, download real image files, pipe them into the live <strong>/api/check-payment</strong> engine, and benchmark expected ground-truth labels against actual detection verdicts.
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <span
              className="evidence-tag observed"
              style={{
                background: "rgba(14, 165, 233, 0.15)",
                color: "var(--brand-cyan)",
                border: "1px solid rgba(14, 165, 233, 0.3)",
                fontSize: "0.72rem",
                fontWeight: 700,
                letterSpacing: "0.04em"
              }}
            >
              SIMULATION ENVIRONMENT
            </span>
            <span
              className="evidence-tag critical"
              style={{ fontSize: "0.72rem" }}
            >
              SAFE ISOLATED TESTBED
            </span>
          </div>
        </div>
      </div>

      {/* 2. Interactive Generator Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.25rem" }}>
        {/* Left Column: Generator Controls */}
        <div className="glass-panel" style={{ padding: "1.25rem" }}>
          <div className="panel-header" style={{ marginBottom: "1rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Sliders size={18} style={{ color: "var(--brand-primary)" }} />
              <h3 style={{ margin: 0, fontSize: "0.98rem", color: "var(--text-primary)" }}>Scenario Configuration</h3>
            </div>
            <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>RFC-Compliant</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div>
              <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600, display: "block", marginBottom: "0.4rem" }}>
                Attack Vector Scenario
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.45rem" }}>
                {[
                  {
                    id: "BENIGN_BASELINE",
                    title: "Verified Clean Retail Payment",
                    sub: "Legitimate merchant checkout baseline without false positive",
                    tag: "Clean Baseline"
                  },
                  {
                    id: "PHISHING_PAYMENT_LURE",
                    title: "Phishing Payment Verification Lure",
                    sub: "RFC 2606 .test domain gateway impersonation",
                    tag: "Phishing Gateway"
                  },
                  {
                    id: "TAMPERED_AMOUNT",
                    title: "Payment Payload Amount Tampering",
                    sub: "Visual bait ₹5,000 vs underlying QR ₹500",
                    tag: "Bait & Switch"
                  },
                  {
                    id: "UNVERIFIED_MULE",
                    title: "Mule Account Drain & Rapid Outflow",
                    sub: "Unverified payee hub with rapid velocity proxy",
                    tag: "Mule Infrastructure"
                  }
                ].map((sc) => {
                  const isSelected = scenarioType === sc.id;
                  return (
                    <div
                      key={sc.id}
                      onClick={() => {
                        setScenarioType(sc.id);
                        generateSimulatedQR(sc.id);
                      }}
                      style={{
                        padding: "0.75rem",
                        borderRadius: "var(--radius-md)",
                        cursor: "pointer",
                        background: isSelected ? "var(--brand-primary-subtle)" : "rgba(255, 255, 255, 0.02)",
                        border: `1px solid ${isSelected ? "var(--brand-primary)" : "var(--border-subtle)"}`,
                        transition: "all 0.15s ease"
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <strong style={{ fontSize: "0.82rem", color: isSelected ? "var(--text-primary)" : "var(--text-secondary)" }}>
                          {sc.title}
                        </strong>
                        <span className="evidence-tag observed" style={{ fontSize: "0.62rem" }}>{sc.tag}</span>
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", marginTop: "3px" }}>
                        {sc.sub}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600, display: "block", marginBottom: "0.4rem" }}>
                Custom Simulation Seed / Txn ID (Optional)
              </label>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  type="text"
                  placeholder="e.g. DEMO-FIN-2026"
                  value={customTxn}
                  onChange={(e) => setCustomTxn(e.target.value)}
                  style={{
                    flex: 1,
                    padding: "0.5rem 0.75rem",
                    background: "rgba(0, 0, 0, 0.3)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-sm)",
                    color: "var(--text-primary)",
                    fontSize: "0.82rem",
                    fontFamily: "JetBrains Mono, monospace"
                  }}
                />
                <button
                  className="btn btn-secondary"
                  onClick={() => generateSimulatedQR(scenarioType)}
                  disabled={generating}
                  style={{ fontSize: "0.78rem", whiteSpace: "nowrap" }}
                >
                  <RefreshCw size={13} className={generating ? "spin" : ""} style={{ marginRight: "4px" }} />
                  Regenerate
                </button>
              </div>
            </div>

            {errorMsg && (
              <div style={{ padding: "0.6rem 0.8rem", background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "var(--radius-sm)", color: "var(--color-high-risk)", fontSize: "0.78rem" }}>
                ⚠️ {errorMsg}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Artifact Preview & Ground Truth */}
        <div className="glass-panel" style={{ padding: "1.25rem" }}>
          <div className="panel-header" style={{ marginBottom: "1rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <QrCode size={18} style={{ color: "var(--brand-cyan)" }} />
              <h3 style={{ margin: 0, fontSize: "0.98rem", color: "var(--text-primary)" }}>Generated Artifact & Payload</h3>
            </div>
            {qrArtifact && (
              <span className="evidence-tag critical" style={{ fontSize: "0.68rem" }}>
                Expected: {qrArtifact.ground_truth_label}
              </span>
            )}
          </div>

          {qrArtifact ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div style={{ display: "flex", gap: "1.25rem", alignItems: "center", flexWrap: "wrap" }}>
                {/* QR Image Box */}
                <div
                  style={{
                    background: "#ffffff",
                    padding: "0.6rem",
                    borderRadius: "var(--radius-md)",
                    display: "inline-flex",
                    boxShadow: "0 4px 14px rgba(0,0,0,0.4)"
                  }}
                >
                  <img
                    src={qrArtifact.qr_data_uri}
                    alt="Simulated Attack QR"
                    style={{ width: "140px", height: "140px", display: "block" }}
                  />
                </div>

                {/* Artifact Details */}
                <div style={{ flex: 1, minWidth: "180px", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>Artifact ID</div>
                  <div style={{ fontSize: "0.85rem", color: "var(--brand-cyan)", fontFamily: "monospace", fontWeight: 700 }}>
                    {qrArtifact.simulation_id}
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600, marginTop: "4px" }}>Category</div>
                  <div style={{ fontSize: "0.82rem", color: "var(--text-primary)" }}>
                    {qrArtifact.category}
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "2px" }}>
                    File: {qrArtifact.file_name} ({qrArtifact.file_size_bytes} bytes)
                  </div>

                  <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
                    <button
                      className="btn btn-secondary"
                      onClick={handleDownloadPNG}
                      style={{ fontSize: "0.75rem", padding: "0.35rem 0.65rem", display: "flex", alignItems: "center", gap: "0.35rem" }}
                    >
                      <Download size={13} />
                      Download PNG
                    </button>
                    {onSendToDetection && (
                      <button
                        className="btn btn-secondary"
                        onClick={() => onSendToDetection(qrArtifact.decoded_payload)}
                        style={{ fontSize: "0.75rem", padding: "0.35rem 0.65rem", display: "flex", alignItems: "center", gap: "0.35rem" }}
                      >
                        <ExternalLink size={13} />
                        Open in Center
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Decoded Payload Box */}
              <div style={{ background: "rgba(0, 0, 0, 0.35)", padding: "0.75rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600, marginBottom: "4px" }}>
                  Decoded QR Payload String
                </div>
                <div style={{ fontSize: "0.78rem", fontFamily: "JetBrains Mono, monospace", color: "var(--brand-cyan)", wordBreak: "break-all" }}>
                  {qrArtifact.decoded_payload}
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "6px" }}>
                  {qrArtifact.description}
                </div>
              </div>

              {/* Submit for Analysis Action */}
              <button
                className="attack-sim-btn"
                onClick={handleRunEvaluation}
                disabled={evaluating}
                style={{ width: "100%", padding: "0.75rem", fontSize: "0.88rem", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}
              >
                {evaluating ? (
                  <>
                    <RefreshCw size={15} className="spin" />
                    Executing Live Forensic Pipeline...
                  </>
                ) : (
                  <>
                    <Play size={15} />
                    Submit for Analysis → Execute /api/check-payment
                  </>
                )}
              </button>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)", fontSize: "0.85rem" }}>
              Generating initial simulated artifact...
            </div>
          )}
        </div>
      </div>

      {/* 3. Real Pipeline Comparison & Benchmark Card */}
      <AnimatePresence>
        {evalResult && compVerdict && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="glass-panel"
            style={{
              padding: "1.25rem",
              border: `1px solid ${compVerdict.color}`,
              background: "rgba(15, 23, 42, 0.75)"
            }}
          >
            <div className="panel-header" style={{ marginBottom: "1rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <Activity size={20} style={{ color: compVerdict.color }} />
                <h3 style={{ margin: 0, fontSize: "1.05rem", color: "var(--text-primary)" }}>
                  Ground-Truth vs Live Pipeline Verdict Comparison
                </h3>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <span
                  style={{
                    background: `${compVerdict.color}22`,
                    color: compVerdict.color,
                    border: `1px solid ${compVerdict.color}`,
                    borderRadius: "4px",
                    padding: "3px 8px",
                    fontSize: "0.72rem",
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    gap: "4px"
                  }}
                >
                  {compVerdict.icon}
                  {compVerdict.badge}
                </span>
              </div>
            </div>

            {/* Comparison Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.75rem", marginBottom: "1rem" }}>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "0.75rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Expected Ground Truth
                </div>
                <div style={{ fontSize: "1.05rem", fontWeight: 800, color: "var(--color-high-risk)", marginTop: "4px", fontFamily: "JetBrains Mono" }}>
                  {qrArtifact?.ground_truth_label}
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "3px" }}>
                  Pre-configured red-team scenario
                </div>
              </div>

              <div style={{ background: "rgba(0,0,0,0.3)", padding: "0.75rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Actual Detection Decision
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "4px" }}>
                  <span className={`decision-pill ${evalResult.decision?.toLowerCase()}`}>
                    {evalResult.decision}
                  </span>
                  <strong style={{ fontSize: "1.05rem", fontFamily: "JetBrains Mono", color: evalResult.risk_score >= 70 ? "var(--color-high-risk)" : (evalResult.risk_score >= 40 ? "var(--color-caution)" : "var(--color-safe)") }}>
                    {evalResult.risk_score}%
                  </strong>
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "3px" }}>
                  Live multi-signal fused score
                </div>
              </div>

              <div style={{ background: "rgba(0,0,0,0.3)", padding: "0.75rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Quantum Escalation Gate
                </div>
                <div style={{ fontSize: "0.92rem", fontWeight: 700, color: "var(--brand-cyan)", marginTop: "4px" }}>
                  {evalResult.quantum_escalation?.escalation_status || "BYPASSED"}
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "3px" }}>
                  {evalResult.quantum_escalation?.statevector_simulator_active ? "Qiskit Statevector Evaluated" : "Fast-Path Evaluated"}
                </div>
              </div>

              <div style={{ background: "rgba(0,0,0,0.3)", padding: "0.75rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Case Registration
                </div>
                <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)", fontFamily: "monospace", marginTop: "4px" }}>
                  {evalResult.case_id}
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "3px" }}>
                  Persisted to immutable audit trail
                </div>
              </div>
            </div>

            {/* Triggered Signals List */}
            {evalResult.risk_signals && evalResult.risk_signals.length > 0 && (
              <div style={{ background: "rgba(0,0,0,0.25)", padding: "0.75rem", borderRadius: "6px", border: "1px solid var(--border-subtle)", marginBottom: "0.75rem" }}>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600, marginBottom: "0.4rem" }}>
                  Triggered Forensic Signals ({evalResult.risk_signals.length})
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                  {evalResult.risk_signals.map((sig, idx) => (
                    <span
                      key={idx}
                      className={`evidence-tag ${sig.severity === "CRITICAL" ? "critical" : (sig.severity === "HIGH" ? "critical" : "moderate")}`}
                      style={{ fontSize: "0.68rem" }}
                    >
                      {sig.name} ({sig.severity})
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Verdict Explanation Summary */}
            <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              <strong>Evaluation Summary:</strong> {compVerdict.summary}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
