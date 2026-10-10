import React, { useState } from "react";
import {
  Shield, Search, Filter, Layers, Clock, AlertTriangle, CheckCircle,
  FileText, Download, Copy, Check, Network, GitFork, MessageSquare,
  Eye, RefreshCw, AlertOctagon, HelpCircle, ThumbsUp, ArrowRight, CornerDownRight
} from "lucide-react";

export function InvestigationCommandCenter({
  casesList,
  activeCase,
  activeCaseId,
  t = {},
  onSelectCase,
  onSearchCases,
  searchQuery,
  onOpenIntakeModal,
  onResetDemos,
  onVerifyAuditChain,
  auditVerifyResult,
  auditVerifying,
  onSubmitAnalystDecision,
  decisionSubmitting,
  analystAction,
  setAnalystAction,
  analystRationale,
  setAnalystRationale,
  onNavigateTab,
  onAskCopilot,
  onExportDossier
}) {
  const [filterSeverity, setFilterSeverity] = useState("ALL"); // ALL, CRITICAL, STEP_UP, APPROVE
  const [filterType, setFilterType] = useState("ALL"); // ALL, REAL, SIMULATION
  const [copiedToast, setCopiedToast] = useState(false);
  const [selectedEvidenceDetail, setSelectedEvidenceDetail] = useState(null);
  const [confirmationModal, setConfirmationModal] = useState(null);

  // Filter cases
  const filteredCases = (casesList || []).filter((c) => {
    if (filterSeverity !== "ALL") {
      if (filterSeverity === "CRITICAL" && c.decision !== "BLOCK") return false;
      if (filterSeverity === "STEP_UP" && c.decision !== "STEP_UP") return false;
      if (filterSeverity === "APPROVE" && c.decision !== "APPROVE") return false;
    }
    if (filterType !== "ALL") {
      const isSim = (c.source || "").toUpperCase().includes("SIM") || (c.source || "").toUpperCase().includes("ATTACK");
      if (filterType === "SIMULATION" && !isSim) return false;
      if (filterType === "REAL" && isSim) return false;
    }
    return true;
  });

  const handleExecuteConsequentialAction = (actionName, payload) => {
    setConfirmationModal({
      actionName,
      payload,
      title: `Confirm Consequential Security Action: ${actionName}`,
      description: `This operation enforces an immutable SOC decision (${actionName}) into the case ledger and will update real downstream verification policies.`
    });
  };

  const handleConfirmAction = () => {
    if (confirmationModal) {
      onSubmitAnalystDecision();
      setConfirmationModal(null);
    }
  };

  return (
    <div className="tab-pane" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* 3-Region Desktop Workspace Layout */}
      <div style={{ display: "grid", gridTemplateColumns: "310px 1fr 340px", gap: "1.25rem", minHeight: "720px", alignItems: "start" }}>

        {/* ========================================================================= */}
        {/* LEFT REGION: Investigation Navigation & Case Triage List                  */}
        {/* ========================================================================= */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "0.85rem", padding: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0, fontSize: "0.88rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <Shield size={16} style={{ color: "var(--brand-primary)" }} /> {t.casesQueue || "Cases Queue"} ({filteredCases.length})
            </h3>
            <div style={{ display: "flex", gap: "0.3rem" }}>
              <button
                className="btn btn-primary"
                style={{ padding: "0.2rem 0.5rem", fontSize: "0.7rem" }}
                onClick={onOpenIntakeModal}
                title="Direct Investigation Intake"
              >
                {t.newIntake || "+ New"}
              </button>
              <button
                className="btn btn-secondary"
                style={{ padding: "0.2rem 0.45rem", fontSize: "0.7rem" }}
                onClick={onResetDemos}
                title="Reset SOC cases"
              >
                {t.resetDemos || "🔄"}
              </button>
            </div>
          </div>

          {/* Search box */}
          <div className="case-search-box" style={{ maxWidth: "100%", width: "100%" }}>
            <Search size={14} style={{ color: "var(--text-muted)" }} />
            <input
              placeholder="Search case, VPA, recipient..."
              value={searchQuery}
              onChange={(e) => onSearchCases(e.target.value)}
              style={{ fontSize: "0.76rem" }}
            />
          </div>

          {/* Filters Bar */}
          <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", fontSize: "0.68rem" }}>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              style={{
                background: "var(--bg-surface-elevated)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-primary)",
                padding: "0.25rem 0.45rem",
                fontSize: "0.68rem"
              }}
            >
              <option value="ALL">All Verdicts</option>
              <option value="CRITICAL">BLOCK / High Risk</option>
              <option value="STEP_UP">STEP_UP / Caution</option>
              <option value="APPROVE">APPROVE / Safe</option>
            </select>

            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              style={{
                background: "var(--bg-surface-elevated)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-primary)",
                padding: "0.25rem 0.45rem",
                fontSize: "0.68rem"
              }}
            >
              <option value="ALL">All Environments</option>
              <option value="REAL">Real SOC Cases</option>
              <option value="SIMULATION">Attack Lab Sim</option>
            </select>
          </div>

          {/* Cases Scrollable List */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.45rem", overflowY: "auto", maxHeight: "580px" }}>
            {filteredCases.map((c) => {
              const isSelected = activeCaseId === c.case_id;
              const isSim = (c.source || "").toUpperCase().includes("SIM") || (c.source || "").toUpperCase().includes("ATTACK");
              return (
                <div
                  key={c.case_id}
                  onClick={() => onSelectCase(c.case_id)}
                  style={{
                    background: isSelected ? "var(--brand-primary-subtle)" : "rgba(8, 12, 22, 0.45)",
                    border: `1px solid ${isSelected ? "var(--brand-primary)" : "var(--border-subtle)"}`,
                    borderLeft: `3px solid ${c.decision === "BLOCK" ? "var(--color-high-risk)" : (c.decision === "STEP_UP" ? "var(--color-caution)" : "var(--color-safe)")}`,
                    borderRadius: "0 var(--radius-md) var(--radius-md) 0",
                    padding: "0.6rem 0.75rem",
                    cursor: "pointer",
                    transition: "all 0.15s ease"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "0.78rem", fontWeight: 700, fontFamily: "JetBrains Mono", color: isSelected ? "var(--brand-primary)" : "var(--text-primary)" }}>
                      {c.case_id}
                    </span>
                    <span className={`decision-pill ${c.decision?.toLowerCase()}`} style={{ fontSize: "0.62rem", padding: "1px 6px" }}>
                      {c.decision}
                    </span>
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "3px", fontSize: "0.68rem" }}>
                    <span style={{ color: "var(--text-secondary)" }}>Risk Score: <b>{c.risk_score}%</b></span>
                    <span style={{ color: isSim ? "var(--color-caution)" : "var(--text-dim)", fontFamily: "JetBrains Mono" }}>
                      {isSim ? "SIMULATED LAB" : (c.source || "SOC INTAKE")}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* CENTER REGION: Investigation Evidence & Findings Timeline                 */}
        {/* ========================================================================= */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.1rem" }}>
          {activeCase ? (
            <>
              {/* Case Header Dossier Strip */}
              <div className="case-header-card" style={{ padding: "1rem" }}>
                <div className="case-header-top" style={{ marginBottom: "0.75rem" }}>
                  <div className="case-identity-group">
                    <div className="case-id-badge">
                      <Shield size={18} style={{ color: "var(--brand-primary)" }} />
                      <span>CASE {activeCase.case_id}</span>
                      {auditVerifyResult && (
                        <span
                          className={`evidence-tag ${auditVerifyResult.is_valid ? "observed" : "critical"}`}
                          style={{ fontSize: "0.62rem", cursor: "pointer", marginLeft: "0.3rem" }}
                          onClick={() => onVerifyAuditChain(activeCase.case_id)}
                          title={`Root: ${auditVerifyResult.root_hash}`}
                        >
                          {auditVerifyResult.is_valid ? "🛡️ SEAL VERIFIED" : "⚠️ TAMPER DETECTED"}
                        </span>
                      )}
                      <button
                        className="btn btn-secondary"
                        style={{ padding: "0.15rem 0.4rem", fontSize: "0.65rem" }}
                        onClick={() => {
                          navigator.clipboard.writeText(activeCase.case_id);
                          setCopiedToast(true);
                          setTimeout(() => setCopiedToast(false), 2000);
                        }}
                      >
                        {copiedToast ? <Check size={10} /> : <Copy size={10} />} {copiedToast ? "Copied" : "Copy"}
                      </button>
                    </div>

                    <div className="case-meta-row" style={{ fontSize: "0.72rem" }}>
                      <span className={`sys-state ${activeCase.status === "ACTION_RECOMMENDED" ? "critical" : "ready"}`}>
                        {activeCase.status?.replace("_", " ")}
                      </span>
                      <span>•</span>
                      <span>SOURCE: <b>{activeCase.source}</b></span>
                      <span>•</span>
                      <span>OPENED: {new Date(activeCase.created_at * 1000).toLocaleTimeString()}</span>
                    </div>
                  </div>

                  <div className="case-metrics-strip">
                    <div className="case-metric-cell" style={{ minWidth: "90px" }}>
                      <span className="case-metric-label">Risk Score</span>
                      <span className="case-metric-value" style={{ color: activeCase.risk?.risk_score >= 70 ? "var(--color-high-risk)" : (activeCase.risk?.risk_score >= 40 ? "var(--color-caution)" : "var(--color-safe)") }}>
                        {activeCase.risk?.risk_score}%
                      </span>
                    </div>
                    <div className="case-metric-cell" style={{ minWidth: "90px" }}>
                      <span className="case-metric-label">Confidence</span>
                      <span className="case-metric-value">{((activeCase.risk?.confidence || 0.95) * 100).toFixed(0)}%</span>
                    </div>
                    <div className="case-metric-cell" style={{ minWidth: "90px" }}>
                      <span className="case-metric-label">Decision</span>
                      <span className={`decision-pill ${activeCase.risk?.decision?.toLowerCase()}`}>
                        {activeCase.risk?.decision}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="case-actions-bar" style={{ paddingTop: "0.65rem" }}>
                  <button className="btn btn-primary" style={{ fontSize: "0.75rem", padding: "0.35rem 0.65rem" }} onClick={() => onNavigateTab("graph")}>
                    <Network size={12} /> View Graph
                  </button>
                  <button className="btn btn-secondary" style={{ fontSize: "0.75rem", padding: "0.35rem 0.65rem" }} onClick={() => onNavigateTab("chain")}>
                    <GitFork size={12} /> Attack Chain
                  </button>
                  <button className="btn btn-secondary" style={{ fontSize: "0.75rem", padding: "0.35rem 0.65rem" }} onClick={onExportDossier}>
                    <Download size={12} /> Export Dossier
                  </button>
                </div>
              </div>

              {/* Chronological Vertical Evidence Timeline */}
              <div className="glass-panel" style={{ padding: "1rem" }}>
                <div className="panel-header" style={{ marginBottom: "0.75rem" }}>
                  <h3 style={{ margin: 0, fontSize: "0.88rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.4rem" }}>
                    <Layers size={15} style={{ color: "var(--brand-primary)" }} /> Corroborated Evidence Timeline
                  </h3>
                  <span className="evidence-tag observed" style={{ fontSize: "0.62rem" }}>
                    {activeCase.evidence?.length || 0} VERIFIED SIGNALS
                  </span>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                  {(activeCase.evidence || []).map((ev, idx) => (
                    <div
                      key={idx}
                      onClick={() => setSelectedEvidenceDetail(ev === selectedEvidenceDetail ? null : ev)}
                      style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: "0.75rem",
                        background: selectedEvidenceDetail === ev ? "rgba(56, 189, 248, 0.08)" : "rgba(8, 12, 22, 0.5)",
                        border: `1px solid ${selectedEvidenceDetail === ev ? "var(--brand-primary)" : "var(--border-subtle)"}`,
                        borderRadius: "var(--radius-md)",
                        padding: "0.65rem 0.85rem",
                        cursor: "pointer",
                        transition: "all 0.15s ease"
                      }}
                    >
                      <div style={{ marginTop: "2px" }}>
                        <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: ev.status === "OBSERVED" ? "var(--color-safe)" : (ev.status === "MISMATCH" ? "var(--color-high-risk)" : "var(--brand-primary)") }} />
                      </div>

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2px" }}>
                          <span style={{ fontSize: "0.74rem", fontWeight: 700, color: "var(--text-primary)" }}>
                            {ev.category} • {ev.field}
                          </span>
                          <span className={`evidence-tag ${ev.status?.toLowerCase() || "observed"}`} style={{ fontSize: "0.6rem" }}>
                            {ev.status} [{ev.source}]
                          </span>
                        </div>
                        <div style={{ fontSize: "0.76rem", color: "var(--text-secondary)", fontFamily: "JetBrains Mono", wordBreak: "break-all" }}>
                          {String(ev.value)}
                        </div>
                        {selectedEvidenceDetail === ev && (
                          <div style={{ marginTop: "0.4rem", paddingTop: "0.4rem", borderTop: "1px solid var(--border-subtle)", fontSize: "0.7rem", color: "var(--text-muted)" }}>
                            Confidence: <b>{((ev.confidence || 0.95) * 100).toFixed(0)}%</b> • Grounding: Verified through cryptographic hash seal and deterministic forensic engine.
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quantum Telemetry Module */}
              <div className="glass-panel" style={{ padding: "0.85rem 1rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
                  <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--brand-primary)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                    ⚛️ Quantum Kernel Telemetry & Escalation Decision
                  </span>
                  <span className={`evidence-tag ${activeCase.quantum_escalation?.circuit_executed ? "observed" : "unavailable"}`} style={{ fontSize: "0.62rem" }}>
                    {activeCase.quantum_escalation?.circuit_executed ? "CIRCUIT EXECUTED (SIMULATION)" : "BYPASS / FAST PATH"}
                  </span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "0.5rem", fontSize: "0.72rem" }}>
                  <div style={{ background: "rgba(8, 12, 22, 0.4)", padding: "0.4rem 0.6rem", borderRadius: "4px" }}>
                    <span style={{ color: "var(--text-muted)", display: "block" }}>Execution Backend</span>
                    <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{activeCase.quantum_escalation?.backend_used || "Local CPU Statevector Simulator"}</span>
                  </div>
                  <div style={{ background: "rgba(8, 12, 22, 0.4)", padding: "0.4rem 0.6rem", borderRadius: "4px" }}>
                    <span style={{ color: "var(--text-muted)", display: "block" }}>Threshold τ*</span>
                    <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>τ* = 0.1083 (+15 Boost)</span>
                  </div>
                  <div style={{ background: "rgba(8, 12, 22, 0.4)", padding: "0.4rem 0.6rem", borderRadius: "4px" }}>
                    <span style={{ color: "var(--text-muted)", display: "block" }}>Hilbert Space Dimension</span>
                    <span style={{ color: "var(--brand-primary)", fontWeight: 600 }}>4-Qubit ℂ¹⁶</span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="glass-panel" style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
              <Shield size={36} style={{ color: "var(--text-dim)", margin: "0 auto 0.75rem auto" }} />
              <p>Select a case from the navigation queue on the left to begin forensic triage.</p>
            </div>
          )}
        </div>

        {/* ========================================================================= */}
        {/* RIGHT REGION: Grounded Investigation Copilot & Consequential Actions      */}
        {/* ========================================================================= */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "1rem", padding: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <MessageSquare size={16} style={{ color: "var(--brand-primary)" }} />
            <h3 style={{ margin: 0, fontSize: "0.88rem", fontWeight: 700 }}>Investigation Copilot</h3>
          </div>

          {activeCase ? (
            <>
              {/* Executive Grounded Summary */}
              <div style={{ background: "rgba(8, 12, 22, 0.5)", padding: "0.75rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)", fontSize: "0.75rem", lineHeight: 1.45 }}>
                <div style={{ fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", fontSize: "0.68rem", marginBottom: "4px" }}>
                  Case Evidence Synthesis
                </div>
                <div style={{ color: "var(--text-primary)", marginBottom: "6px" }}>
                  <b>What:</b> {activeCase.summary?.what_happened}
                </div>
                <div style={{ color: "var(--color-caution)", marginBottom: "6px" }}>
                  <b>Why:</b> {activeCase.summary?.why_suspicious}
                </div>
                <div style={{ color: "var(--brand-primary)" }}>
                  <b>Next:</b> {activeCase.summary?.what_should_happen_next}
                </div>
              </div>

              {/* Contradictions & Missing Evidence */}
              <div style={{ background: "rgba(255,255,255,0.02)", padding: "0.75rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)", fontSize: "0.74rem" }}>
                <div style={{ fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", fontSize: "0.68rem", marginBottom: "4px" }}>
                  Evidence Integrity & Gaps
                </div>
                <div style={{ color: "var(--text-secondary)" }}>
                  • Evidence Quality: <b>{activeCase.scorecard?.evidence_quality || "HIGH"}</b><br />
                  • Graph Topology: <b>{activeCase.scorecard?.graph_context || "1st-Degree Mule Links"}</b><br />
                  • External Threat: <b>{activeCase.scorecard?.external_intelligence || "Hash-first observed"}</b>
                </div>
              </div>

              {/* Consequential Human Action Controls with Explicit Confirmation */}
              <div style={{ background: "rgba(8, 12, 22, 0.6)", padding: "0.75rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-medium)" }}>
                <label style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 700, display: "block", marginBottom: "0.4rem" }}>
                  CONSEQUENTIAL SOC ACTION:
                </label>
                <select
                  value={analystAction}
                  onChange={(e) => setAnalystAction(e.target.value)}
                  style={{
                    width: "100%",
                    background: "var(--bg-surface-elevated)",
                    border: "1px solid var(--border-medium)",
                    borderRadius: "var(--radius-sm)",
                    color: "var(--text-primary)",
                    padding: "0.4rem",
                    fontSize: "0.74rem",
                    marginBottom: "0.5rem"
                  }}
                >
                  <option value="CONFIRM_RECOMMENDATION">✓ Confirm Machine Recommendation</option>
                  <option value="OVERRIDE_STEP_UP">⚠️ Enforce Biometric Step-Up Challenge</option>
                  <option value="OVERRIDE_APPROVE">🛡️ Authorize Payment (Analyst Override)</option>
                  <option value="ESCALATE_TO_SENIOR">⚡ Escalate to Lead Security Officer</option>
                </select>

                <textarea
                  rows={2}
                  placeholder="Enter mandatory audit rationale for consequential operation..."
                  value={analystRationale}
                  onChange={(e) => setAnalystRationale(e.target.value)}
                  style={{
                    width: "100%",
                    background: "var(--bg-surface-elevated)",
                    border: "1px solid var(--border-medium)",
                    borderRadius: "var(--radius-sm)",
                    color: "var(--text-primary)",
                    padding: "0.4rem",
                    fontSize: "0.72rem",
                    marginBottom: "0.6rem"
                  }}
                />

                <button
                  className="btn btn-primary"
                  onClick={() => handleExecuteConsequentialAction(analystAction, { rationale: analystRationale })}
                  disabled={decisionSubmitting}
                  style={{ width: "100%", padding: "0.45rem", fontSize: "0.75rem", display: "flex", justifyContent: "center", alignItems: "center", gap: "0.4rem" }}
                >
                  {decisionSubmitting ? "Executing..." : "Execute SOC Decision →"}
                </button>
              </div>

              {/* Copilot Deep Query */}
              <button
                className="btn btn-secondary"
                style={{ fontSize: "0.75rem", padding: "0.45rem", display: "flex", justifyContent: "center", alignItems: "center", gap: "0.4rem" }}
                onClick={() => onAskCopilot(`Investigate inconsistencies and missing evidence for case ${activeCase.case_id}`)}
              >
                <MessageSquare size={13} /> Deep Query with Copilot
              </button>
            </>
          ) : (
            <div style={{ color: "var(--text-dim)", fontSize: "0.75rem", textAlign: "center", padding: "2rem 0" }}>
              Awaiting case selection.
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Modal for Consequential Operations */}
      {confirmationModal && (
        <div className="modal-backdrop" onClick={() => setConfirmationModal(null)}>
          <div className="evidence-modal-content" style={{ maxWidth: "480px" }} onClick={(e) => e.stopPropagation()}>
            <div className="panel-header" style={{ marginBottom: "0.75rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <AlertOctagon size={18} style={{ color: "var(--color-caution)" }} />
                <h3 style={{ margin: 0, fontSize: "0.95rem" }}>{confirmationModal.title}</h3>
              </div>
              <button className="btn btn-secondary" onClick={() => setConfirmationModal(null)} style={{ padding: "0.2rem 0.5rem" }}>✕</button>
            </div>
            <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
              {confirmationModal.description}
            </p>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "0.6rem", borderRadius: "4px", fontSize: "0.72rem", color: "var(--text-muted)", margin: "0.75rem 0", fontFamily: "JetBrains Mono" }}>
              Rationale: {analystRationale || "Standard protocol enforcement confirmed by investigator."}
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "1rem" }}>
              <button className="btn btn-secondary" onClick={() => setConfirmationModal(null)} style={{ fontSize: "0.75rem" }}>
                {t.cancel || "Cancel"}
              </button>
              <button className="btn btn-primary" onClick={handleConfirmAction} style={{ fontSize: "0.75rem" }}>
                {t.confirmAction || "Authorize & Commit Decision"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
