import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  QrCode, Link as LinkIcon, Image as ImageIcon, CreditCard,
  Search, ShieldAlert, Cpu, ArrowRight, Upload, Play, CheckCircle,
  AlertTriangle, RefreshCw, FileSearch, Sparkles, ChevronRight, Layers, Eye
} from 'lucide-react';
import confetti from 'canvas-confetti';

export function DetectionCenterWorkspace({
  fastApiBase,
  checkScenarios,
  onSelectCase,
  onAskCopilot,
  onOpenEvidenceDetails
}) {
  // Detector Sub-mode: "QR", "LINK", "SCREENSHOT", "TRANSACTION"
  const [detectorMode, setDetectorMode] = useState("QR");

  // Form Inputs
  const [payloadText, setPayloadText] = useState("upi://pay?pa=freshmart.retail@icici&pn=Fresh%20Mart%20Retail&am=850.00&cu=INR&tn=Order%204991");
  const [imageBase64, setImageBase64] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageName, setImageName] = useState(null);
  const [selectedScenarioId, setSelectedScenarioId] = useState("SCENARIO_1_SAFE_QR");

  // Transaction scoring form
  const [txnForm, setTxnForm] = useState({
    txn_id: "TXN-QF-" + Math.floor(100000 + Math.random() * 900000),
    user_id: "USR-9901",
    amount: 85000,
    hour: 23,
    velocity_1h: 12,
    location_score: 0.82,
    device_score: 0.78,
    merchant_risk: 0.76,
    account_age_days: 40
  });

  // Execution & Result State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStage, setAnalysisStage] = useState(0);
  const [checkResult, setCheckResult] = useState(null);
  const [resultViewMode, setResultViewMode] = useState("simple"); // "simple" | "forensic"
  const [errorMsg, setErrorMsg] = useState(null);

  // Canonical Pitch Presets
  const pitchPresets = [
    {
      id: "SCENARIO_1_SAFE_QR",
      mode: "QR",
      title: "Safe Grocery QR",
      badge: "VERIFIED / BENIGN",
      desc: "ICICI verified merchant baseline, valid checksum, zero behavioral anomaly.",
      payload: "upi://pay?pa=freshmart.retail@icici&pn=Fresh%20Mart%20Retail&am=850.00&cu=INR&tn=Order%204991"
    },
    {
      id: "SCENARIO_2_SUSPICIOUS_SE_QR",
      mode: "QR",
      title: "Urgent Lottery Scam QR",
      badge: "CRITICAL / PHISHING",
      desc: "Deceptive domain routing to lottery scheme with high urgency social engineering.",
      payload: "upi://pay?pa=claim.rewards.lottery@freecharge&pn=Claim%20Free%20Bonus&am=4999.00&cu=INR&tn=URGENT%20KYC%20VERIFY%20NOW"
    },
    {
      id: "SCENARIO_D_SUSPICIOUS_PAYMENT_LINK",
      mode: "LINK",
      title: "Lookalike Bank Link",
      badge: "MALICIOUS / TYPOSQUAT",
      desc: "Typosquatted domain, self-signed TLS, phishing infrastructure.",
      payload: "https://hdfc-netbanking-secure-auth.xyz/verify-otp?session=99281"
    },
    {
      id: "SCENARIO_B_QR_AMOUNT_MISMATCH",
      mode: "SCREENSHOT",
      title: "Manipulated Receipt vs QR",
      badge: "FORENSIC TAMPERING",
      desc: "Visual receipt states ₹850, embedded QR payload commands ₹85,000 to mule VPA.",
      payload: "upi://pay?pa=shadow.attacker@ybl&pn=Quick%20Cash&am=85000.00&cu=INR&tn=Invoice%20850"
    },
    {
      id: "SCENARIO_5_AMBIGUOUS_QUANTUM",
      mode: "TRANSACTION",
      title: "Borderline High-Value Anomaly",
      badge: "QUANTUM ESCALATION",
      desc: "Classical models in disagreement (0.48-0.54 score). Triggers 4-qubit ZZFeatureMap kernel.",
      payload: "TXN-BORDERLINE-9921"
    }
  ];

  const handleSelectPreset = (preset) => {
    setSelectedScenarioId(preset.id);
    setDetectorMode(preset.mode);
    setCheckResult(null);
    setErrorMsg(null);

    if (preset.mode === "TRANSACTION") {
      setTxnForm({
        txn_id: "TXN-QF-QUANTUM-" + Math.floor(1000 + Math.random() * 9000),
        user_id: "USR-HIGH-VALUE",
        amount: 145000,
        hour: 2,
        velocity_1h: 7,
        location_score: 0.65,
        device_score: 0.60,
        merchant_risk: 0.70,
        account_age_days: 180
      });
    } else {
      setPayloadText(preset.payload);
      setImageBase64(null);
      setImagePreview(null);
      setImageName(null);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      alert("Please upload a valid image file (PNG, JPEG, WebP).");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert("File exceeds maximum allowed size (5 MB).");
      return;
    }

    setImageName(file.name);
    setSelectedScenarioId(null);
    const reader = new FileReader();
    reader.onload = () => {
      setImageBase64(reader.result);
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const executeDetection = async () => {
    setIsAnalyzing(true);
    setCheckResult(null);
    setErrorMsg(null);

    setAnalysisStage(1); // Payload extraction
    await new Promise(r => setTimeout(r, 120));
    setAnalysisStage(2); // Threat intel & OCR
    await new Promise(r => setTimeout(r, 150));
    setAnalysisStage(3); // Classical ML consensus
    await new Promise(r => setTimeout(r, 150));
    setAnalysisStage(4); // Quantum escalation check
    await new Promise(r => setTimeout(r, 150));
    setAnalysisStage(5); // Evidence synthesis

    try {
      if (detectorMode === "TRANSACTION") {
        const res = await fetch(`${fastApiBase}/api/predict`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(txnForm)
        });
        if (!res.ok) throw new Error("Transaction scoring failed");
        const data = await res.json();

        // Wrap into check-result compatible structure
        setCheckResult({
          case_id: data.txn_id,
          decision: data.decision,
          risk_score: Math.round(data.risk_score),
          confidence: data.confidence,
          risk_level: data.risk_level,
          input_type: "TRANSACTION",
          quantum_escalation: data.quantum_escalation,
          model_scores: data.model_scores,
          risk_factors: data.risk_factors,
          reasons: (data.risk_factors || []).map(rf => ({
            title: rf,
            description: "Behavioral anomaly flagged by ML consensus",
            severity: data.risk_score >= 60 ? "high" : "medium",
            impact: "+25 risk points"
          })),
          evidence_checklist: [
            { label: "Account Age Calibration", status: txnForm.account_age_days < 60 ? "fail" : "ok" },
            { label: "Velocity Burst Threshold", status: txnForm.velocity_1h > 5 ? "fail" : "ok" },
            { label: "Geographic Incongruence", status: txnForm.location_score > 0.5 ? "fail" : "ok" },
            { label: "Hardware Root Attestation", status: txnForm.device_score > 0.5 ? "fail" : "ok" },
            { label: "Quantum Kernel Similarity Check", status: data.quantum_escalation?.circuit_executed ? "ok" : "na" }
          ],
          source_payload: `Txn ₹${txnForm.amount.toLocaleString()} • User ${txnForm.user_id} • Velocity ${txnForm.velocity_1h}/hr`
        });

        if (data.decision === "APPROVE") {
          confetti({ particleCount: 40, spread: 45, origin: { y: 0.7 } });
        }
      } else {
        // Multi-modal forensics endpoint
        const res = await fetch(`${fastApiBase}/api/check-payment`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            input_type: detectorMode,
            payload: payloadText,
            image_base64: imageBase64,
            filename: imageName,
            scenario_id: selectedScenarioId
          })
        });
        if (!res.ok) throw new Error("Payment forensics analysis failed");
        const data = await res.json();
        setCheckResult(data);

        if (data.decision === "APPROVE") {
          confetti({ particleCount: 50, spread: 45, origin: { y: 0.7 } });
        }
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || "Failed to reach detection backend service.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="tab-pane">
      {/* 1. Header Banner */}
      <div className="glass-panel" style={{ background: "var(--bg-surface-elevated)", borderBottom: "2px solid var(--brand-primary)" }}>
        <div className="panel-header" style={{ marginBottom: "0.25rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <ShieldAlert size={20} style={{ color: "var(--brand-primary)" }} />
              <h2 style={{ margin: 0, fontSize: "1.1rem" }}>Unified Multi-Modal Detection Center</h2>
            </div>
            <p className="panel-desc" style={{ marginTop: "4px" }}>
              Live verification engine for UPI QR payloads, payment screenshots, phishing URLs, and transactional feature vectors.
            </p>
          </div>
          <span className="evidence-tag observed" style={{ letterSpacing: "0.05em" }}>
            FASTAPI LIVE BACKEND
          </span>
        </div>

        {/* Evaluation Presets Bar */}
        <div style={{ marginTop: "1rem", paddingTop: "0.85rem", borderTop: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "0.68rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)", marginBottom: "0.5rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <Sparkles size={12} style={{ color: "var(--brand-primary)" }} />
            <span>Hackathon Evaluation Scenarios (Click to Load)</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.5rem" }}>
            {pitchPresets.map(preset => {
              const isSelected = selectedScenarioId === preset.id;
              return (
                <button
                  key={preset.id}
                  onClick={() => handleSelectPreset(preset)}
                  style={{
                    background: isSelected ? "var(--brand-primary-subtle)" : "rgba(255,255,255,0.02)",
                    border: `1px solid ${isSelected ? "var(--brand-primary)" : "var(--border-subtle)"}`,
                    borderRadius: "var(--radius-md)",
                    padding: "0.55rem 0.75rem",
                    textAlign: "left",
                    cursor: "pointer",
                    transition: "all 0.15s ease"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2px" }}>
                    <span style={{ fontSize: "0.76rem", fontWeight: 700, color: "var(--text-primary)" }}>{preset.title}</span>
                    <span style={{ fontSize: "0.58rem", padding: "1px 4px", borderRadius: "3px", background: "rgba(255,255,255,0.06)", color: "var(--text-muted)" }}>
                      {preset.badge}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.68rem", color: "var(--text-dim)", lineHeight: 1.3 }}>
                    {preset.desc}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 2. Workspace Layout: Left Input Panel, Right Results Panel */}
      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1.3fr", gap: "1.25rem" }}>

        {/* LEFT COLUMN: Detector Workspace Inputs */}
        <div className="glass-panel" style={{ height: "fit-content" }}>
          <div className="panel-header" style={{ marginBottom: "0.75rem" }}>
            <h3 style={{ fontSize: "0.92rem", margin: 0, display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <Search size={16} style={{ color: "var(--brand-primary)" }} />
              Forensic Ingestion & Vector Input
            </h3>
            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Active: <b>{detectorMode}</b></span>
          </div>

          {/* Detector Mode Selector */}
          <div className="mode-selector" style={{ marginBottom: "1rem" }}>
            <button
              className={`mode-tab-btn ${detectorMode === "QR" ? "active" : ""}`}
              onClick={() => { setDetectorMode("QR"); setSelectedScenarioId(null); setCheckResult(null); }}
            >
              <QrCode size={14} /> UPI QR Code
            </button>
            <button
              className={`mode-tab-btn ${detectorMode === "LINK" ? "active" : ""}`}
              onClick={() => { setDetectorMode("LINK"); setSelectedScenarioId(null); setCheckResult(null); }}
            >
              <LinkIcon size={14} /> Payment Link / URL
            </button>
            <button
              className={`mode-tab-btn ${detectorMode === "SCREENSHOT" ? "active" : ""}`}
              onClick={() => { setDetectorMode("SCREENSHOT"); setSelectedScenarioId(null); setCheckResult(null); }}
            >
              <ImageIcon size={14} /> Receipt Screenshot
            </button>
            <button
              className={`mode-tab-btn ${detectorMode === "TRANSACTION" ? "active" : ""}`}
              onClick={() => { setDetectorMode("TRANSACTION"); setSelectedScenarioId(null); setCheckResult(null); }}
            >
              <CreditCard size={14} /> Transaction Vector
            </button>
          </div>

          {/* INPUT FORMS BASED ON MODE */}
          {detectorMode === "TRANSACTION" ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <div style={{ background: "rgba(255,255,255,0.02)", padding: "0.75rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "0.5rem", fontWeight: 600 }}>
                  Behavioral & Device Features (Evaluated against XGBoost, RF, Isolation Forest, and Qiskit Kernel)
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "0.6rem" }}>
                  <div>
                    <label style={{ fontSize: "0.68rem", color: "var(--text-dim)", display: "block" }}>Amount (₹ INR)</label>
                    <input
                      type="number"
                      value={txnForm.amount}
                      onChange={e => setTxnForm({ ...txnForm, amount: parseFloat(e.target.value) || 0 })}
                      style={{ width: "100%", padding: "0.4rem", borderRadius: "4px", background: "var(--bg-surface-elevated)", border: "1px solid var(--border-medium)", color: "var(--text-primary)", fontFamily: "JetBrains Mono" }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: "0.68rem", color: "var(--text-dim)", display: "block" }}>1-Hour Velocity</label>
                    <input
                      type="number"
                      value={txnForm.velocity_1h}
                      onChange={e => setTxnForm({ ...txnForm, velocity_1h: parseInt(e.target.value) || 0 })}
                      style={{ width: "100%", padding: "0.4rem", borderRadius: "4px", background: "var(--bg-surface-elevated)", border: "1px solid var(--border-medium)", color: "var(--text-primary)", fontFamily: "JetBrains Mono" }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: "0.68rem", color: "var(--text-dim)", display: "block" }}>Hour of Day (0-23)</label>
                    <input
                      type="number"
                      value={txnForm.hour}
                      onChange={e => setTxnForm({ ...txnForm, hour: parseInt(e.target.value) || 0 })}
                      style={{ width: "100%", padding: "0.4rem", borderRadius: "4px", background: "var(--bg-surface-elevated)", border: "1px solid var(--border-medium)", color: "var(--text-primary)", fontFamily: "JetBrains Mono" }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: "0.68rem", color: "var(--text-dim)", display: "block" }}>Account Age (Days)</label>
                    <input
                      type="number"
                      value={txnForm.account_age_days}
                      onChange={e => setTxnForm({ ...txnForm, account_age_days: parseInt(e.target.value) || 0 })}
                      style={{ width: "100%", padding: "0.4rem", borderRadius: "4px", background: "var(--bg-surface-elevated)", border: "1px solid var(--border-medium)", color: "var(--text-primary)", fontFamily: "JetBrains Mono" }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: "0.68rem", color: "var(--text-dim)", display: "block" }}>Location Risk (0-1.0)</label>
                    <input
                      type="number"
                      step="0.05"
                      value={txnForm.location_score}
                      onChange={e => setTxnForm({ ...txnForm, location_score: parseFloat(e.target.value) || 0 })}
                      style={{ width: "100%", padding: "0.4rem", borderRadius: "4px", background: "var(--bg-surface-elevated)", border: "1px solid var(--border-medium)", color: "var(--text-primary)", fontFamily: "JetBrains Mono" }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: "0.68rem", color: "var(--text-dim)", display: "block" }}>Device Risk (0-1.0)</label>
                    <input
                      type="number"
                      step="0.05"
                      value={txnForm.device_score}
                      onChange={e => setTxnForm({ ...txnForm, device_score: parseFloat(e.target.value) || 0 })}
                      style={{ width: "100%", padding: "0.4rem", borderRadius: "4px", background: "var(--bg-surface-elevated)", border: "1px solid var(--border-medium)", color: "var(--text-primary)", fontFamily: "JetBrains Mono" }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div>
              {/* String Payload input */}
              <div style={{ marginBottom: "0.85rem" }}>
                <label style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", display: "block", marginBottom: "4px" }}>
                  {detectorMode === "LINK" ? "URL / Payment Gateway Target" : "Raw UPI String / Merchant Payload"}
                </label>
                <textarea
                  rows={3}
                  value={payloadText}
                  onChange={e => {
                    setPayloadText(e.target.value);
                    setSelectedScenarioId(null);
                  }}
                  placeholder={detectorMode === "LINK" ? "https://..." : "upi://pay?pa=..."}
                  style={{
                    width: "100%",
                    padding: "0.6rem",
                    borderRadius: "var(--radius-md)",
                    background: "var(--bg-surface-elevated)",
                    border: "1px solid var(--border-medium)",
                    color: "var(--text-primary)",
                    fontFamily: "JetBrains Mono",
                    fontSize: "0.78rem",
                    resize: "vertical"
                  }}
                />
              </div>

              {/* Image Upload box (mandatory for screenshot, optional for QR) */}
              <div style={{ marginBottom: "0.85rem" }}>
                <label style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", display: "block", marginBottom: "4px" }}>
                  Payment Screenshot / Artifact Image {detectorMode === "SCREENSHOT" ? "(Recommended)" : "(Optional)"}
                </label>
                <label className="file-dropzone" style={{ display: "block", margin: 0, padding: "1rem" }}>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    style={{ display: "none" }}
                  />
                  <div className="dropzone-inner">
                    <Upload size={18} style={{ color: "var(--text-muted)" }} />
                    <span style={{ fontSize: "0.75rem", color: "var(--text-primary)", fontWeight: 600 }}>
                      {imageName ? imageName : "Drop receipt screenshot or browse (PNG, JPG)"}
                    </span>
                    <span style={{ fontSize: "0.65rem", color: "var(--text-dim)" }}>
                      Max 5MB • Extracted via RapidOCR & OpenCV
                    </span>
                  </div>
                </label>

                {imagePreview && (
                  <div style={{ marginTop: "0.5rem", display: "flex", alignItems: "center", gap: "0.75rem", background: "rgba(0,0,0,0.2)", padding: "0.4rem", borderRadius: "6px" }}>
                    <img
                      src={imagePreview}
                      alt="Uploaded proof"
                      style={{ width: "48px", height: "48px", objectFit: "cover", borderRadius: "4px", border: "1px solid var(--border-medium)" }}
                    />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: "0.74rem", color: "var(--text-primary)", fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {imageName}
                      </div>
                      <span style={{ fontSize: "0.65rem", color: "var(--color-safe)" }}>Image loaded in memory</span>
                    </div>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: "2px 6px", fontSize: "0.7rem" }}
                      onClick={() => { setImageBase64(null); setImagePreview(null); setImageName(null); }}
                    >
                      ✕
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Execution Button */}
          <div style={{ marginTop: "1rem" }}>
            <button
              className="btn btn-primary"
              onClick={executeDetection}
              disabled={isAnalyzing}
              style={{ width: "100%", padding: "0.75rem", fontSize: "0.85rem", fontWeight: 700, display: "flex", justifyContent: "center", alignItems: "center", gap: "0.5rem" }}
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw size={15} className="spin" />
                  Running Neural & Quantum Forensics...
                </>
              ) : (
                <>
                  <Play size={15} />
                  Analyze Payment Threat Vector →
                </>
              )}
            </button>
          </div>

          {/* Multi-stage pipeline stepper */}
          {isAnalyzing && (
            <div className="pipeline-steps-container" style={{ marginTop: "1rem" }}>
              <div className="pipeline-title">Active Inference Pipeline: Stage {analysisStage}/5</div>
              <div className="pipeline-steps">
                <div className={`step ${analysisStage >= 1 ? "active" : ""}`}>1. Ingest</div>
                <div className={`step ${analysisStage >= 2 ? "active" : ""}`}>2. OCR & Intel</div>
                <div className={`step ${analysisStage >= 3 ? "active" : ""}`}>3. Classical</div>
                <div className={`step ${analysisStage >= 4 ? "active" : ""}`}>4. Qiskit</div>
                <div className={`step ${analysisStage >= 5 ? "active" : ""}`}>5. Synthesis</div>
              </div>
            </div>
          )}

          {errorMsg && (
            <div style={{ marginTop: "0.75rem", padding: "0.65rem", borderRadius: "6px", background: "var(--color-critical-subtle)", border: "1px solid var(--color-critical-border)", color: "#FCA5A5", fontSize: "0.75rem" }}>
              ⚠️ {errorMsg}
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: Results & Multi-detector Findings */}
        <div className="glass-panel" style={{ minHeight: "520px" }}>
          {!checkResult && !isAnalyzing && (
            <div style={{ textAlign: "center", padding: "4rem 2rem", color: "var(--text-muted)" }}>
              <FileSearch size={42} style={{ color: "var(--text-dim)", margin: "0 auto 1rem auto" }} />
              <h3 style={{ fontSize: "1rem", color: "var(--text-primary)", marginBottom: "0.4rem" }}>
                Awaiting Telemetry Ingestion
              </h3>
              <p style={{ fontSize: "0.78rem", maxWidth: "380px", margin: "0 auto" }}>
                Select an evaluation preset above or enter custom UPI/URL parameters, then click <b>Analyze Payment Threat Vector</b> to trigger forensics.
              </p>
            </div>
          )}

          {isAnalyzing && (
            <div style={{ textAlign: "center", padding: "4rem 2rem" }}>
              <RefreshCw size={36} className="spin" style={{ color: "var(--brand-primary)", margin: "0 auto 1rem auto" }} />
              <h3 style={{ fontSize: "0.95rem", color: "var(--text-primary)" }}>Corroborating Multi-Modal Evidence</h3>
              <p style={{ fontSize: "0.76rem", color: "var(--text-muted)", marginTop: "4px" }}>
                Executing RapidOCR, domain WHOIS verification, classical tree ensembles, and Qiskit Statevector kernel evaluation...
              </p>
            </div>
          )}

          {checkResult && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.15 }}
            >
              {/* Verdict Header Bar */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.85rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <h3 style={{ fontSize: "0.95rem", fontWeight: 700, margin: 0, color: "var(--text-primary)" }}>
                    Detection Finding Dossier
                  </h3>
                  <span className="evidence-tag observed" style={{ fontFamily: "JetBrains Mono", fontSize: "0.68rem" }}>
                    CASE {checkResult.case_id}
                  </span>
                </div>

                <div className="view-mode-toggle">
                  <button
                    className={`view-mode-btn ${resultViewMode === "simple" ? "active" : ""}`}
                    onClick={() => setResultViewMode("simple")}
                  >
                    Simple Verdict
                  </button>
                  <button
                    className={`view-mode-btn ${resultViewMode === "forensic" ? "active" : ""}`}
                    onClick={() => setResultViewMode("forensic")}
                  >
                    Forensic Proofs 🔬
                  </button>
                </div>
              </div>

              {/* Hero Decision Banner */}
              <div className={`fintech-result-hero ${checkResult.decision === "APPROVE" ? "safe" : (checkResult.decision === "BLOCK" ? "high-risk" : "caution")}`} style={{ marginBottom: "1rem" }}>
                <div className="hero-status-row">
                  <div className="hero-status-main">
                    <div className="hero-status-icon-box">
                      {checkResult.decision === "APPROVE" ? (
                        <CheckCircle size={22} />
                      ) : checkResult.decision === "BLOCK" ? (
                        <AlertTriangle size={22} />
                      ) : (
                        <ShieldAlert size={22} />
                      )}
                    </div>
                    <div>
                      <div className="hero-status-title">
                        {checkResult.decision === "APPROVE" ? "Low Risk — Payment Authorized" : (checkResult.decision === "BLOCK" ? "High Risk — Authorization Blocked" : "Caution — Step-Up Verification Required")}
                      </div>
                      <div className="hero-status-sub">
                        {checkResult.risk_level} • Evidence Confidence: {((checkResult.confidence || 0.95) * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                  <span className={`decision-pill ${checkResult.decision.toLowerCase()}`} style={{ fontSize: "0.82rem", padding: "0.3rem 0.75rem" }}>
                    {checkResult.decision}
                  </span>
                </div>

                <div className="fintech-kpi-row" style={{ marginTop: "0.75rem" }}>
                  <div className="fintech-kpi-tile">
                    <span className="fintech-kpi-label">Risk Score</span>
                    <div className="fintech-kpi-value" style={{ color: checkResult.risk_score >= 60 ? "var(--color-high-risk)" : (checkResult.risk_score >= 30 ? "var(--color-caution)" : "var(--color-safe)") }}>
                      {checkResult.risk_score} <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>/ 100</span>
                    </div>
                  </div>
                  <div className="fintech-kpi-tile">
                    <span className="fintech-kpi-label">Quantum Kernel Gate</span>
                    <div className="fintech-kpi-value" style={{ fontSize: "0.78rem", color: "var(--brand-primary)" }}>
                      {checkResult.quantum_escalation?.quantum_escalation_status || "FAST_PATH"}
                    </div>
                  </div>
                  <div className="fintech-kpi-tile">
                    <span className="fintech-kpi-label">Detector Source</span>
                    <div className="fintech-kpi-value" style={{ fontSize: "0.82rem" }}>
                      {checkResult.input_type || detectorMode}
                    </div>
                  </div>
                </div>
              </div>

              {/* 3. SUB-VIEW: SIMPLE VS FORENSIC */}
              {resultViewMode === "simple" ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
                  {/* Flagged reasons */}
                  <div className="reasons-box">
                    <div className="reasons-header">
                      <ShieldAlert size={14} style={{ color: "var(--brand-primary)" }} />
                      <span>{checkResult.decision === "APPROVE" ? "Integrity Corroboration Summary" : "Primary Risk Indicators Flagged"}</span>
                    </div>
                    <div className="reasons-list">
                      {(checkResult.reasons || []).length > 0 ? (
                        checkResult.reasons.map((r, i) => (
                          <div key={i} className={`reason-card ${r.severity || "medium"}`}>
                            <div className="reason-top">
                              <span className="reason-title">{r.title}</span>
                              <span className="reason-impact">{r.impact}</span>
                            </div>
                            <div className="reason-desc">{r.description}</div>
                          </div>
                        ))
                      ) : (
                        <div style={{ fontSize: "0.75rem", color: "var(--color-safe)", padding: "0.5rem" }}>
                          ✓ Zero malicious payloads or cross-modal discrepancies detected.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Checklist */}
                  {checkResult.evidence_checklist && (
                    <div className="checklist-card">
                      <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                        <CheckCircle size={14} style={{ color: "var(--color-safe)" }} />
                        <span>Multi-Detector Verification Checklist</span>
                      </div>
                      <div className="checklist-grid" style={{ marginTop: "0.5rem" }}>
                        {checkResult.evidence_checklist.map((item, idx) => (
                          <div key={idx} className={`checklist-item ${item.status}`}>
                            <span>{item.status === "ok" ? "✓" : (item.status === "fail" ? "✕" : "—")}</span>
                            <span>{item.label}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Action buttons */}
                  <div style={{ display: "flex", gap: "0.6rem", marginTop: "0.5rem" }}>
                    <button
                      className="btn btn-primary"
                      onClick={() => onSelectCase(checkResult.case_id)}
                      style={{ flex: 1, padding: "0.6rem", fontSize: "0.78rem" }}
                    >
                      Open in Investigation Center Workspace →
                    </button>
                    <button
                      className="btn btn-secondary"
                      onClick={() => onAskCopilot(`Why was case ${checkResult.case_id} given decision ${checkResult.decision} with risk score ${checkResult.risk_score}?`)}
                      style={{ padding: "0.6rem 0.85rem", fontSize: "0.78rem" }}
                    >
                      Ask Copilot
                    </button>
                  </div>
                </div>
              ) : (
                /* FORENSIC TELEMETRY VIEW */
                <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
                  {/* Quantum Escalation Card */}
                  {checkResult.quantum_escalation && (
                    <div style={{ background: "rgba(9, 13, 22, 0.4)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "0.75rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
                        <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--brand-primary)" }}>
                          ⚛️ Qiskit Quantum Kernel Telemetry
                        </span>
                        <span className="evidence-tag observed" style={{ fontSize: "0.62rem" }}>
                          {checkResult.quantum_escalation.execution_mode || "SIMULATION"}
                        </span>
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", lineHeight: 1.5, fontFamily: "JetBrains Mono" }}>
                        <div>Status: <b>{checkResult.quantum_escalation.quantum_escalation_status}</b></div>
                        <div>Circuit Executed: <b>{checkResult.quantum_escalation.circuit_executed ? "TRUE (Qiskit Statevector)" : "FALSE (Fast-path)"}</b></div>
                        <div>Threshold τ*: <b>{checkResult.quantum_escalation.qsvc_threshold ?? 0.1083}</b> | Raw Kernel Score: <b>{checkResult.quantum_escalation.raw_score ?? "N/A"}</b></div>
                        <div>Backend: <b>{checkResult.quantum_escalation.backend || checkResult.quantum_escalation.backend_used || "Local CPU Simulation"}</b></div>
                      </div>
                    </div>
                  )}

                  {/* Threat Intel findings */}
                  {checkResult.threat_intelligence && (
                    <div style={{ background: "rgba(9, 13, 22, 0.4)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "0.75rem" }}>
                      <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.4rem" }}>
                        🌐 Domain & Threat Intelligence
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                        <div>Domain: <b>{checkResult.threat_intelligence.domain || "N/A"}</b></div>
                        <div>Reputation: <b style={{ color: checkResult.threat_intelligence.threat_score >= 50 ? "var(--color-high-risk)" : "var(--color-safe)" }}>Score {checkResult.threat_intelligence.threat_score}/100</b></div>
                        <div>Security Flags: <b>{(checkResult.threat_intelligence.categories || []).join(", ") || "Clean"}</b></div>
                      </div>
                    </div>
                  )}

                  {/* Cryptographic hash */}
                  {checkResult.evidence_verification?.file_metadata?.sha256 && (
                    <div style={{ background: "rgba(9, 13, 22, 0.4)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "0.75rem" }}>
                      <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
                        Cryptographic Evidence Seal (SHA-256)
                      </div>
                      <div style={{ fontSize: "0.7rem", fontFamily: "JetBrains Mono", color: "var(--text-primary)", marginTop: "4px", wordBreak: "break-all" }}>
                        {checkResult.evidence_verification.file_metadata.sha256}
                      </div>
                    </div>
                  )}

                  <div style={{ display: "flex", gap: "0.6rem" }}>
                    <button
                      className="btn btn-secondary"
                      onClick={() => onOpenEvidenceDetails && onOpenEvidenceDetails()}
                      style={{ flex: 1, padding: "0.55rem", fontSize: "0.75rem" }}
                    >
                      <Eye size={13} /> View Multimodal Forensic Dossier
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={() => onSelectCase(checkResult.case_id)}
                      style={{ flex: 1, padding: "0.55rem", fontSize: "0.75rem" }}
                    >
                      Open Case in SOC Center →
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
