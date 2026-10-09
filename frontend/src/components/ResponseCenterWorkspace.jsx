import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldAlert, ShieldCheck, AlertTriangle, CheckCircle2, Info,
  Lock, FileText, Download, ExternalLink, Eye, ArrowRight,
  Clock, UserCheck, RefreshCw, Bot, Copy, Check, ChevronRight,
  AlertCircle, Shield, FileCheck, Layers
} from 'lucide-react';

export default function ResponseCenterWorkspace({
  currentCaseId = "QF-20261007-49910",
  onNavigateTab,
  onAskCopilot
}) {
  const [caseId, setCaseId] = useState(currentCaseId);
  const [responseMode, setResponseMode] = useState("simple"); // "simple" | "analyst"
  const [responseData, setResponseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Analyst Decision Form
  const [analystAction, setAnalystAction] = useState("CONFIRM_RECOMMENDATION");
  const [analystRationale, setAnalystRationale] = useState("");
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [decisionSuccessMsg, setDecisionSuccessMsg] = useState(null);

  // Copy feedback
  const [copiedEvidence, setCopiedEvidence] = useState(false);

  // Load Response Data
  const loadResponseData = async (targetCaseId) => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`http://127.0.0.1:8000/api/investigation/cases/${targetCaseId}/response`);
      if (!res.ok) {
        throw new Error(`Failed to load response data for case ${targetCaseId} (HTTP ${res.status})`);
      }
      const data = await res.json();
      setResponseData(data);
    } catch (err) {
      console.error("Error fetching response center data:", err);
      setError(err.message || "Failed to load response center data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentCaseId) {
      setCaseId(currentCaseId);
      loadResponseData(currentCaseId);
    }
  }, [currentCaseId]);

  // Record an action in the case audit trail
  const handleRecordAction = async (actionName, details) => {
    try {
      await fetch(`http://127.0.0.1:8000/api/investigation/cases/${caseId}/actions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action_name: actionName,
          actor: "ANALYST",
          details: details
        })
      });
      // Refresh to update audit trail
      loadResponseData(caseId);
    } catch (err) {
      console.warn("Could not record action in audit trail:", err);
    }
  };

  // Submit Analyst Decision
  const handleSubmitDecision = async (e) => {
    e.preventDefault();
    if (!analystRationale.trim()) {
      alert("Please provide an investigation rationale for your decision.");
      return;
    }
    try {
      setSubmittingDecision(true);
      const res = await fetch(`http://127.0.0.1:8000/api/investigation/cases/${caseId}/analyst-decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analyst_action: analystAction,
          rationale: analystRationale.trim(),
          author: "Lead SOC Analyst"
        })
      });
      if (!res.ok) throw new Error("Failed to submit analyst decision.");
      setDecisionSuccessMsg("Analyst decision recorded successfully in audit history.");
      setAnalystRationale("");
      setTimeout(() => setDecisionSuccessMsg(null), 4000);
      loadResponseData(caseId);
    } catch (err) {
      alert(err.message);
    } finally {
      setSubmittingDecision(false);
    }
  };

  // Download Forensic Dossier Report
  const handleDownloadReport = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/investigation/cases/${caseId}/report`);
      if (!res.ok) throw new Error("Failed to fetch report.");
      const report = await res.json();
      
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `QF-Report-${caseId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      handleRecordAction("Forensic Dossier Exported", "Downloaded 11-section JSON forensic investigation report.");
    } catch (err) {
      alert("Failed to export report: " + err.message);
    }
  };

  // Copy Evidence Summary Markdown
  const handleCopyEvidenceMarkdown = () => {
    if (!responseData?.evidence_package?.summary_markdown) return;
    navigator.clipboard.writeText(responseData.evidence_package.summary_markdown);
    setCopiedEvidence(true);
    setTimeout(() => setCopiedEvidence(false), 2500);
    handleRecordAction("Evidence Package Copied", "Copied markdown evidence table to clipboard for external reporting.");
  };

  if (loading && !responseData) {
    return (
      <div className="glass-panel" style={{ padding: "3rem", textAlign: "center" }}>
        <RefreshCw className="animate-spin" size={24} style={{ color: "var(--brand-primary)", margin: "0 auto 1rem auto" }} />
        <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>Loading Response Center Recommendations for {caseId}...</p>
      </div>
    );
  }

  if (error || !responseData) {
    return (
      <div className="glass-panel" style={{ padding: "2rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", color: "var(--color-high-risk)", marginBottom: "1rem" }}>
          <AlertCircle size={20} />
          <h3 style={{ fontSize: "1rem", margin: 0 }}>Response Center Unavailable</h3>
        </div>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "1.5rem" }}>
          {error || "No active case selected or response recommendations could not be calculated."}
        </p>
        <button className="btn btn-secondary" onClick={() => loadResponseData(caseId)}>
          <RefreshCw size={14} /> Retry Loading
        </button>
      </div>
    );
  }

  const {
    recommendation,
    action_cards = [],
    playbook = [],
    evidence_package,
    audit_trail = [],
    analyst_decision,
    simple_view_guide,
    limitations = [],
    boundary_disclaimer
  } = responseData;

  const isHighRisk = recommendation.risk_level === "HIGH" || recommendation.risk_level === "CRITICAL";
  const isMedRisk = recommendation.risk_level === "MEDIUM";

  return (
    <div className="response-center-workspace">
      {/* Top Header */}
      <div className="glass-panel" style={{ marginBottom: "1.25rem", padding: "1.25rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.25rem" }}>
              <ShieldAlert size={20} style={{ color: isHighRisk ? "var(--color-high-risk)" : (isMedRisk ? "var(--color-caution)" : "var(--color-safe)") }} />
              <h2 style={{ fontSize: "1.2rem", fontWeight: 600, margin: 0, color: "var(--text-primary)" }}>
                RESPONSE CENTER
              </h2>
              <span className={`evidence-tag ${isHighRisk ? 'critical' : (isMedRisk ? 'moderate' : 'observed')}`}>
                {recommendation.risk_level}
              </span>
            </div>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", margin: 0 }}>
              Recommended next steps based on available evidence and authoritative risk fusion.
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            {/* View Mode Switcher */}
            <div className="tab-pill-group" style={{ background: "var(--bg-app)", padding: "2px", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
              <button
                className={`tab-pill ${responseMode === "simple" ? "active" : ""}`}
                style={{ fontSize: "0.78rem", padding: "0.35rem 0.75rem" }}
                onClick={() => setResponseMode("simple")}
              >
                <UserCheck size={13} style={{ marginRight: "4px" }} /> Simple View
              </button>
              <button
                className={`tab-pill ${responseMode === "analyst" ? "active" : ""}`}
                style={{ fontSize: "0.78rem", padding: "0.35rem 0.75rem" }}
                onClick={() => setResponseMode("analyst")}
              >
                <Layers size={13} style={{ marginRight: "4px" }} /> Analyst View
              </button>
            </div>

            <button
              className="btn btn-secondary"
              style={{ fontSize: "0.78rem", padding: "0.4rem 0.75rem" }}
              onClick={() => loadResponseData(caseId)}
              title="Refresh Response Recommendations"
            >
              <RefreshCw size={13} />
            </button>
          </div>
        </div>

        {/* Top Case Summary Bar */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "0.75rem",
          marginTop: "1.25rem",
          paddingTop: "1rem",
          borderTop: "1px solid var(--border-subtle)"
        }}>
          <div className="case-metric-card" style={{ padding: "0.6rem 0.8rem", background: "var(--bg-surface-elevated)", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>CASE ID</span>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>{caseId}</div>
          </div>

          <div className="case-metric-card" style={{ padding: "0.6rem 0.8rem", background: "var(--bg-surface-elevated)", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>RISK SCORE</span>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: isHighRisk ? "var(--color-high-risk)" : (isMedRisk ? "var(--color-caution)" : "var(--color-safe)"), marginTop: "2px" }}>
              {recommendation.risk_score.toFixed(1)}% <span style={{ fontSize: "0.75rem", fontWeight: 400, color: "var(--text-muted)" }}>({recommendation.risk_level})</span>
            </div>
          </div>

          <div className="case-metric-card" style={{ padding: "0.6rem 0.8rem", background: "var(--bg-surface-elevated)", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>CONFIDENCE</span>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
              {recommendation.confidence_level} <span style={{ fontSize: "0.75rem", fontWeight: 400, color: "var(--text-muted)" }}>({(recommendation.confidence_score * 100).toFixed(0)}%)</span>
            </div>
          </div>

          <div className="case-metric-card" style={{ padding: "0.6rem 0.8rem", background: "var(--bg-surface-elevated)", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>EVIDENCE QUALITY</span>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
              {recommendation.evidence_quality}
            </div>
          </div>

          <div className="case-metric-card" style={{ padding: "0.6rem 0.8rem", background: "var(--bg-surface-elevated)", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>AUTH RECOMMENDATION</span>
            <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--brand-primary)", marginTop: "2px" }}>
              {recommendation.verification_recommendation.replace(/_/g, " ")}
            </div>
          </div>
        </div>
      </div>

      {/* Primary Recommended Action Banner */}
      <div className="glass-panel" style={{
        marginBottom: "1.25rem",
        padding: "1.25rem",
        borderLeft: `4px solid ${isHighRisk ? "var(--color-high-risk)" : (isMedRisk ? "var(--color-caution)" : "var(--color-safe)")}`
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <span style={{ fontSize: "0.72rem", fontWeight: 600, letterSpacing: "0.5px", color: "var(--text-muted)", textTransform: "uppercase" }}>
              SYSTEM RECOMMENDATION
            </span>
            <h1 style={{
              fontSize: "1.35rem",
              fontWeight: 700,
              color: isHighRisk ? "var(--color-high-risk)" : (isMedRisk ? "var(--color-caution)" : "var(--color-safe)"),
              margin: "0.2rem 0 0.4rem 0"
            }}>
              {recommendation.primary_action}
            </h1>
            <p style={{ fontSize: "0.85rem", color: "var(--text-primary)", margin: "0 0 0.5rem 0", maxWidth: "800px" }}>
              {recommendation.headline}
            </p>
            <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: 0, maxWidth: "800px" }}>
              {recommendation.rationale}
            </p>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <button
              className="btn btn-secondary"
              style={{ fontSize: "0.78rem" }}
              onClick={() => onNavigateTab && onNavigateTab("investigation")}
            >
              <FileText size={13} /> Open Investigation Center
            </button>
            <button
              className="btn btn-secondary"
              style={{ fontSize: "0.78rem" }}
              onClick={() => onNavigateTab && onNavigateTab("check")}
            >
              <Eye size={13} /> Review Evidence
            </button>
            <button
              className="btn btn-primary"
              style={{ fontSize: "0.78rem" }}
              onClick={() => onAskCopilot && onAskCopilot("What should I do next?", { txn_id: caseId, risk_score: recommendation.risk_score })}
            >
              <Bot size={13} /> Ask Copilot: Next Steps
            </button>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* MODE 1: SIMPLE VIEW (User-friendly 5-10s comprehension)  */}
      {/* ========================================================= */}
      {responseMode === "simple" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* What Should I Do? */}
          <div className="glass-panel" style={{ padding: "1.5rem" }}>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.5rem" }}>
              💡 What Should I Do?
            </h3>
            <p style={{ fontSize: "0.95rem", color: "var(--text-primary)", fontWeight: 500, marginBottom: "0.75rem" }}>
              {simple_view_guide.what_should_i_do}
            </p>
            <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: "1.25rem" }}>
              {simple_view_guide.why_explanation}
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
              {/* What to do now */}
              <div style={{ background: "rgba(16, 185, 129, 0.05)", border: "1px solid rgba(16, 185, 129, 0.2)", borderRadius: "8px", padding: "1.2rem" }}>
                <h4 style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--color-safe)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <CheckCircle2 size={16} /> What to do now
                </h4>
                <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.8rem", color: "var(--text-primary)", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {simple_view_guide.what_to_do_now.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>

              {/* What to avoid */}
              <div style={{ background: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "8px", padding: "1.2rem" }}>
                <h4 style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--color-high-risk)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <AlertTriangle size={16} /> What to avoid
                </h4>
                <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.8rem", color: "var(--text-primary)", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {simple_view_guide.what_to_avoid.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* When to seek help */}
            <div style={{ marginTop: "1.25rem", padding: "0.85rem 1rem", background: "var(--bg-surface-elevated)", borderRadius: "6px", border: "1px solid var(--border-subtle)", fontSize: "0.8rem" }}>
              <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>When to seek additional help: </span>
              <span style={{ color: "var(--text-secondary)" }}>{simple_view_guide.when_to_seek_help}</span>
            </div>
          </div>

          {/* Simple Step-by-Step Guidance */}
          <div className="glass-panel" style={{ padding: "1.25rem" }}>
            <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "1rem" }}>
              📋 Simple Step-by-Step Guidance
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
              {playbook.map((step) => (
                <div
                  key={step.step_number}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: "0.8rem",
                    padding: "0.8rem",
                    background: "var(--bg-surface-elevated)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "6px"
                  }}
                >
                  <div style={{
                    width: "24px",
                    height: "24px",
                    borderRadius: "50%",
                    background: "var(--brand-primary)",
                    color: "#fff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    flexShrink: 0,
                    marginTop: "2px"
                  }}>
                    {step.step_number}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
                        {step.title}
                      </span>
                      <span className={`evidence-tag ${step.status === 'ACTION_RECOMMENDED' ? 'critical' : (step.status === 'COMPLETED' ? 'observed' : 'moderate')}`} style={{ fontSize: "0.68rem" }}>
                        {step.status.replace(/_/g, " ")}
                      </span>
                    </div>
                    <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "0.2rem 0 0 0" }}>
                      {step.instruction}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODE 2: ANALYST VIEW (Full SOC workspace & Evidence Pack) */}
      {/* ========================================================= */}
      {responseMode === "analyst" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          
          {/* Action Cards Grid */}
          <div className="glass-panel" style={{ padding: "1.25rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <div>
                <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
                  🛡️ Action Cards & Recommended Response Workflows
                </h3>
                <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", margin: "2px 0 0 0" }}>
                  Evidence-grounded action triggers categorized by execution type.
                </p>
              </div>
              <span className="evidence-tag observed">6 ACTION OPTIONS</span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "0.85rem" }}>
              {action_cards.map((card) => {
                const isSimulated = card.action_type === "SIMULATED";
                const isExternal = card.action_type === "EXTERNAL_ACTION";
                const isUser = card.action_type === "USER_ACTION";

                return (
                  <div
                    key={card.id}
                    style={{
                      background: "var(--bg-surface-elevated)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "8px",
                      padding: "1rem",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                      gap: "0.75rem"
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.35rem" }}>
                        <h4 style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
                          {card.title}
                        </h4>
                        <span className={`evidence-tag ${isSimulated ? 'moderate' : (isExternal ? 'inferred' : 'critical')}`} style={{ fontSize: "0.68rem" }}>
                          {card.action_type.replace(/_/g, " ")}
                        </span>
                      </div>
                      <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", margin: "0 0 0.5rem 0" }}>
                        {card.description}
                      </p>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", background: "rgba(9, 13, 22, 0.4)", padding: "0.4rem 0.6rem", borderRadius: "4px" }}>
                        <span style={{ fontWeight: 600, color: "var(--text-secondary)" }}>Why: </span>
                        {card.why}
                      </div>
                    </div>

                    <div>
                      {card.disclaimer && (
                        <p style={{ fontSize: "0.68rem", color: "var(--text-muted)", fontStyle: "italic", margin: "0 0 0.5rem 0" }}>
                          * {card.disclaimer}
                        </p>
                      )}
                      {card.action_url ? (
                        <a
                          href={card.action_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn btn-secondary"
                          style={{ width: "100%", justifyContent: "center", fontSize: "0.75rem" }}
                          onClick={() => handleRecordAction(card.title, `Opened external portal ${card.action_url}`)}
                        >
                          <ExternalLink size={12} /> {card.action_button_label}
                        </a>
                      ) : (
                        <button
                          className={`btn ${card.action_type === 'RECOMMENDED' ? 'btn-primary' : 'btn-secondary'}`}
                          style={{ width: "100%", justifyContent: "center", fontSize: "0.75rem" }}
                          onClick={() => {
                            if (card.id === "ACT-PRESERVE-EVIDENCE") {
                              handleDownloadReport();
                            } else {
                              handleRecordAction(card.title, `Triggered action: ${card.action_button_label}`);
                              alert(`Action recorded: ${card.title} (${card.action_button_label})`);
                            }
                          }}
                        >
                          {card.action_button_label}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Response Playbook (Guided Step-by-Step) */}
          <div className="glass-panel" style={{ padding: "1.25rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <div>
                <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
                  📖 SOC Response Playbook
                </h3>
                <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", margin: "2px 0 0 0" }}>
                  Standard operating procedure sequence with forensic evidence grounding.
                </p>
              </div>
              <span className="evidence-tag observed">{playbook.length} STEPS</span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {playbook.map((step) => (
                <div
                  key={step.step_number}
                  style={{
                    background: "var(--bg-surface-elevated)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "6px",
                    padding: "0.85rem 1rem"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.3rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <span style={{
                        background: "var(--brand-primary)",
                        color: "#fff",
                        fontSize: "0.7rem",
                        fontWeight: 700,
                        padding: "2px 6px",
                        borderRadius: "4px"
                      }}>
                        STEP {step.step_number}
                      </span>
                      <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
                        {step.title}
                      </span>
                      <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                        ({step.actor})
                      </span>
                    </div>
                    <span className={`evidence-tag ${step.status === 'ACTION_RECOMMENDED' ? 'critical' : (step.status === 'COMPLETED' ? 'observed' : 'moderate')}`} style={{ fontSize: "0.68rem" }}>
                      {step.status.replace(/_/g, " ")}
                    </span>
                  </div>

                  <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "0.2rem 0 0.5rem 0" }}>
                    {step.instruction}
                  </p>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", fontSize: "0.72rem", background: "rgba(9, 13, 22, 0.4)", padding: "0.4rem 0.6rem", borderRadius: "4px" }}>
                    <div>
                      <span style={{ fontWeight: 600, color: "var(--text-secondary)" }}>Why: </span>
                      <span style={{ color: "var(--text-muted)" }}>{step.why}</span>
                    </div>
                    <div>
                      <span style={{ fontWeight: 600, color: "var(--text-secondary)" }}>Evidence: </span>
                      <span style={{ color: "var(--text-muted)" }}>{step.evidence}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Report & Recover Evidence Package */}
          <div className="glass-panel" style={{ padding: "1.25rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap", gap: "0.5rem" }}>
              <div>
                <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
                  📦 Report & Recover Evidence Package
                </h3>
                <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", margin: "2px 0 0 0" }}>
                  Organized evidence items with verified provenance badges for regulatory/law-enforcement reporting.
                </p>
              </div>

              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: "0.75rem", padding: "0.35rem 0.75rem" }}
                  onClick={handleCopyEvidenceMarkdown}
                >
                  {copiedEvidence ? <Check size={12} style={{ color: "var(--color-safe)" }} /> : <Copy size={12} />}
                  {copiedEvidence ? "Copied Markdown" : "Copy Evidence Summary"}
                </button>
                <button
                  className="btn btn-primary"
                  style={{ fontSize: "0.75rem", padding: "0.35rem 0.75rem" }}
                  onClick={handleDownloadReport}
                >
                  <Download size={12} /> Export 11-Section JSON Dossier
                </button>
              </div>
            </div>

            {/* Evidence items table */}
            <div style={{ overflowX: "auto" }}>
              <table className="evidence-table" style={{ width: "100%", fontSize: "0.78rem" }}>
                <thead>
                  <tr>
                    <th style={{ width: "25%" }}>Evidence Field</th>
                    <th style={{ width: "45%" }}>Value</th>
                    <th style={{ width: "15%" }}>Provenance</th>
                    <th style={{ width: "15%" }}>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {evidence_package.items.map((item, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{item.field_label}</td>
                      <td style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)", wordBreak: "break-all" }}>
                        {typeof item.value === "object" ? JSON.stringify(item.value) : String(item.value)}
                      </td>
                      <td>
                        <span className={`evidence-tag ${
                          item.provenance === "OBSERVED" ? "observed" :
                          item.provenance === "INFERRED" ? "inferred" :
                          item.provenance === "UNAVAILABLE" ? "unavailable" : "synthetic"
                        }`} style={{ fontSize: "0.68rem" }}>
                          [{item.provenance}]
                        </span>
                      </td>
                      <td style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>
                        {item.notes || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Provenance breakdown footer */}
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginTop: "0.75rem",
              paddingTop: "0.75rem",
              borderTop: "1px solid var(--border-subtle)",
              fontSize: "0.72rem",
              color: "var(--text-muted)"
            }}>
              <div style={{ display: "flex", gap: "1rem" }}>
                <span><strong>Observed:</strong> {evidence_package.observed_fields_count} fields</span>
                <span><strong>Inferred:</strong> {evidence_package.inferred_fields_count} axes</span>
                <span><strong>Disclosed Unavailable:</strong> {evidence_package.unavailable_fields_count} items</span>
              </div>
              <span>No fabricated fields or external assumptions.</span>
            </div>
          </div>

          {/* Action Audit Trail & Analyst Decision (2 columns) */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
            
            {/* Real Action History Audit Trail */}
            <div className="glass-panel" style={{ padding: "1.25rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <div>
                  <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
                    ⏱️ Case Action Audit Trail
                  </h3>
                  <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", margin: "2px 0 0 0" }}>
                    Verified session audit log (no simulated timestamps).
                  </p>
                </div>
                <span className="evidence-tag observed">{audit_trail.length} ENTRIES</span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem", maxHeight: "280px", overflowY: "auto" }}>
                {audit_trail.map((entry) => (
                  <div
                    key={entry.entry_id}
                    style={{
                      padding: "0.6rem 0.75rem",
                      background: "var(--bg-surface-elevated)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "6px",
                      fontSize: "0.75rem"
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2px" }}>
                      <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                        {entry.action_name}
                      </span>
                      <span style={{ color: "var(--brand-primary)", fontFamily: "var(--font-mono)", fontSize: "0.7rem" }}>
                        {entry.timestamp_formatted}
                      </span>
                    </div>
                    <p style={{ margin: "2px 0 0 0", color: "var(--text-secondary)", fontSize: "0.72rem" }}>
                      {entry.details}
                    </p>
                    <div style={{ display: "flex", justifyContent: "space-between", marginTop: "4px", fontSize: "0.68rem", color: "var(--text-muted)" }}>
                      <span>Actor: {entry.actor}</span>
                      <span>[{entry.provenance}]</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Analyst Override & Decision Form */}
            <div className="glass-panel" style={{ padding: "1.25rem" }}>
              <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", margin: 0, marginBottom: "0.25rem" }}>
                ✍️ Human Analyst Review & Override
              </h3>
              <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", margin: "0 0 1rem 0" }}>
                Separate human investigator verdict from the system assessment.
              </p>

              {decisionSuccessMsg && (
                <div style={{ padding: "0.6rem", background: "rgba(16, 185, 129, 0.1)", border: "1px solid var(--color-safe)", borderRadius: "6px", color: "var(--color-safe)", fontSize: "0.75rem", marginBottom: "0.75rem" }}>
                  {decisionSuccessMsg}
                </div>
              )}

              {analyst_decision && analyst_decision.analyst_action && (
                <div style={{ padding: "0.6rem 0.8rem", background: "rgba(59, 130, 246, 0.1)", border: "1px solid rgba(59, 130, 246, 0.3)", borderRadius: "6px", fontSize: "0.75rem", marginBottom: "1rem" }}>
                  <div style={{ fontWeight: 600, color: "var(--brand-primary)", marginBottom: "2px" }}>
                    Current Analyst Decision: {analyst_decision.analyst_action}
                  </div>
                  <div style={{ color: "var(--text-secondary)" }}>
                    Status: {analyst_decision.analyst_review_status} | Rationale: {analyst_decision.analyst_rationale || "N/A"}
                  </div>
                </div>
              )}

              <form onSubmit={handleSubmitDecision} style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.25rem" }}>
                    Select Action:
                  </label>
                  <select
                    className="select-input"
                    value={analystAction}
                    onChange={(e) => setAnalystAction(e.target.value)}
                    style={{ width: "100%", padding: "0.4rem", background: "var(--bg-app)", border: "1px solid var(--border-subtle)", borderRadius: "4px", color: "var(--text-primary)", fontSize: "0.78rem" }}
                  >
                    <option value="CONFIRM_RECOMMENDATION">CONFIRM RECOMMENDATION (Endorse System Assessment)</option>
                    <option value="OVERRIDE_STEP_UP">OVERRIDE TO STEP-UP AUTH (Require Secondary MFA)</option>
                    <option value="OVERRIDE_APPROVE">OVERRIDE TO APPROVE (Authorized Exception)</option>
                    <option value="ESCALATE_TO_SENIOR">ESCALATE TO SENIOR FRAUD DESK</option>
                    <option value="DISMISS_FALSE_POSITIVE">DISMISS AS FALSE POSITIVE</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.25rem" }}>
                    Analyst Investigation Rationale:
                  </label>
                  <textarea
                    className="text-input"
                    rows={3}
                    placeholder="Enter explicit rationale for this case decision (e.g. verified merchant over phone)..."
                    value={analystRationale}
                    onChange={(e) => setAnalystRationale(e.target.value)}
                    style={{ width: "100%", padding: "0.4rem", background: "var(--bg-app)", border: "1px solid var(--border-subtle)", borderRadius: "4px", color: "var(--text-primary)", fontSize: "0.78rem" }}
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ width: "100%", justifyContent: "center", fontSize: "0.78rem" }}
                  disabled={submittingDecision}
                >
                  {submittingDecision ? "Recording Decision..." : "Submit Human Analyst Verdict"}
                </button>
              </form>
            </div>
          </div>

          {/* Disclosures & Limitations Footer */}
          <div className="glass-panel" style={{ padding: "1rem 1.25rem", background: "rgba(9, 13, 22, 0.6)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.35rem" }}>
              <Info size={14} style={{ color: "var(--brand-primary)" }} />
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-primary)" }}>
                Epistemic Boundaries & Legal Notice
              </span>
            </div>
            <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", margin: "0 0 0.5rem 0" }}>
              {boundary_disclaimer}
            </p>
            <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.7rem", color: "var(--text-muted)" }}>
              {limitations.map((lim, idx) => (
                <li key={idx}>{lim}</li>
              ))}
            </ul>
          </div>

        </div>
      )}
    </div>
  );
}
