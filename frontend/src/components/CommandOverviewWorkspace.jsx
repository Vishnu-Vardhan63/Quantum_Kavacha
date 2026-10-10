import React from "react";
import {
  Activity, Shield, Eye, Cpu, Network, Zap, Flame, ShieldAlert,
  Server, CheckCircle, AlertTriangle, FileSearch, ArrowRight, Play, RotateCcw
} from "lucide-react";

export function CommandOverviewWorkspace({
  analytics,
  health,
  quantumStatus,
  fraudAlerts,
  recentTxns,
  activeCase,
  casesList,
  t = {},
  onNavigate,
  onSelectCase,
  onRunDetection
}) {
  const activeUnresolvedAlerts = (fraudAlerts || []).filter(
    (a) => a.status === "ACTIVE" || a.status === "TRIGGERED" || a.severity === "CRITICAL"
  );
  const criticalCount = activeUnresolvedAlerts.length;

  return (
    <div className="tab-pane" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* 1. Tactical Ops Banner */}
      <div
        className="glass-panel"
        style={{
          background: "linear-gradient(135deg, rgba(20, 28, 46, 0.95), rgba(13, 19, 34, 0.98))",
          border: "1px solid var(--border-medium)",
          borderLeft: "4px solid var(--brand-primary)",
          padding: "1.25rem"
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Zap size={20} style={{ color: "var(--brand-primary)" }} />
              <h2 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 800, letterSpacing: "-0.01em" }}>
                {t.appName || "Quantum Kavacha"} {t.titleOverview ? `— ${t.titleOverview}` : "Agentic Command Center"}
              </h2>
            </div>
            <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginTop: "4px", maxWidth: "680px", lineHeight: 1.45 }}>
              {t.descOverview || "Continuous multimodal defense coordinating IBM Qiskit Statevector kernel inference, RapidOCR document verification, Rapid Threat Intelligence feeds, and autonomous SOC case triage."}
            </p>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <button
              className="btn btn-primary"
              onClick={() => onNavigate("investigation")}
              style={{ display: "flex", alignItems: "center", gap: "0.4rem", padding: "0.5rem 0.85rem", fontSize: "0.78rem" }}
            >
              <Shield size={14} /> {t.openInvestigation || "Open Investigation Command"} ({casesList?.length || 0})
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => onNavigate("evidence")}
              style={{ display: "flex", alignItems: "center", gap: "0.4rem", padding: "0.5rem 0.85rem", fontSize: "0.78rem" }}
            >
              <Eye size={14} /> {t.ingestVector || "Ingest Evidence Vector"}
            </button>
          </div>
        </div>

        {/* Tactical Key Findings Strip */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.75rem", marginTop: "1.1rem" }}>
          <div style={{ background: "rgba(8, 12, 22, 0.6)", padding: "0.65rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.68rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)" }}>{t.activeInvestigations || "Active Investigations"}</span>
            <div style={{ fontSize: "1.25rem", fontWeight: 800, fontFamily: "JetBrains Mono", color: "var(--text-primary)", marginTop: "2px" }}>
              {casesList?.length || 0}
            </div>
            <span style={{ fontSize: "0.68rem", color: "var(--color-safe)" }}>Real SOC dossiers loaded</span>
          </div>

          <div style={{ background: "rgba(8, 12, 22, 0.6)", padding: "0.65rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.68rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)" }}>{t.criticalThreats || "Critical Threat Incidents"}</span>
            <div style={{ fontSize: "1.25rem", fontWeight: 800, fontFamily: "JetBrains Mono", color: criticalCount > 0 ? "var(--color-high-risk)" : "var(--color-safe)", marginTop: "2px" }}>
              {criticalCount}
            </div>
            <span style={{ fontSize: "0.68rem", color: criticalCount > 0 ? "var(--color-high-risk)" : "var(--text-dim)" }}>
              {criticalCount > 0 ? "Immediate triage required" : "Zero uncontained alerts"}
            </span>
          </div>

          <div style={{ background: "rgba(8, 12, 22, 0.6)", padding: "0.65rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.68rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)" }}>{t.quantumKernelGate || "Quantum Kernel Gate"}</span>
            <div style={{ fontSize: "1.1rem", fontWeight: 800, fontFamily: "JetBrains Mono", color: "var(--brand-primary)", marginTop: "2px" }}>
              {quantumStatus?.execution_mode || "SIMULATION"}
            </div>
            <span style={{ fontSize: "0.68rem", color: "var(--text-dim)" }}>4-Qubit ZZFeatureMap (CPU)</span>
          </div>

          <div style={{ background: "rgba(8, 12, 22, 0.6)", padding: "0.65rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.68rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)" }}>{t.systemIntegrity || "System Integrity"}</span>
            <div style={{ fontSize: "1.1rem", fontWeight: 800, fontFamily: "JetBrains Mono", color: health?.status === "healthy" ? "var(--color-safe)" : "var(--color-caution)", marginTop: "2px" }}>
              {health?.status === "healthy" ? "OPERATIONAL" : "DEGRADED"}
            </div>
            <span style={{ fontSize: "0.68rem", color: "var(--text-dim)" }}>FastAPI + SQLite/Mongo DB</span>
          </div>
        </div>
      </div>

      {/* 2. Priority Split: Active Case Under Review & Threat Queue */}
      <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: "1.25rem" }}>
        {/* Left: Active Primary Case Lead */}
        <div className="glass-panel">
          <div className="panel-header" style={{ marginBottom: "0.85rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <Shield size={16} style={{ color: "var(--brand-primary)" }} />
              <h3 style={{ margin: 0, fontSize: "0.92rem", fontWeight: 700 }}>Primary Active Investigation</h3>
            </div>
            {activeCase && (
              <span className={`decision-pill ${activeCase.risk?.decision?.toLowerCase()}`}>
                {activeCase.risk?.decision} ({activeCase.risk?.risk_score}%)
              </span>
            )}
          </div>

          {activeCase ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(8, 12, 22, 0.5)", padding: "0.65rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                <div>
                  <div style={{ fontSize: "0.88rem", fontWeight: 800, fontFamily: "JetBrains Mono", color: "var(--text-primary)" }}>
                    {activeCase.case_id}
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "2px" }}>
                    Source: <b>{activeCase.source}</b> • Created: {new Date(activeCase.created_at * 1000).toLocaleTimeString()}
                  </div>
                </div>
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: "0.72rem", padding: "0.3rem 0.65rem" }}
                  onClick={() => onNavigate("investigation")}
                >
                  Inspect Case Dossier →
                </button>
              </div>

              {/* Summary Points */}
              <div style={{ background: "rgba(255,255,255,0.02)", padding: "0.75rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)", fontSize: "0.76rem", lineHeight: 1.45 }}>
                <div style={{ color: "var(--text-muted)", fontWeight: 700, fontSize: "0.7rem", textTransform: "uppercase", marginBottom: "4px" }}>
                  Executive Incident Summary
                </div>
                <div style={{ color: "var(--text-secondary)" }}>
                  {activeCase.summary?.what_happened || "Awaiting multi-signal evidentiary synthesis."}
                </div>
                <div style={{ color: "var(--color-caution)", marginTop: "4px" }}>
                  ⚠️ {activeCase.summary?.why_suspicious || "Pending anomaly analysis."}
                </div>
              </div>

              {/* Observed Evidentiary Signals */}
              <div>
                <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "0.4rem" }}>
                  Corroborated Evidence Items ({activeCase.evidence?.length || 0})
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                  {(activeCase.evidence || []).slice(0, 4).map((ev, i) => (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        background: "rgba(8, 12, 22, 0.4)",
                        padding: "0.45rem 0.65rem",
                        borderRadius: "4px",
                        fontSize: "0.74rem"
                      }}
                    >
                      <span style={{ color: "var(--text-secondary)" }}>
                        <b style={{ color: "var(--text-primary)" }}>{ev.category}</b>: {ev.field}
                      </span>
                      <span className={`evidence-tag ${ev.status?.toLowerCase() || "observed"}`} style={{ fontSize: "0.62rem" }}>
                        {ev.status} [{ev.source}]
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-dim)" }}>
              <FileSearch size={28} style={{ margin: "0 auto 0.5rem auto" }} />
              <p style={{ fontSize: "0.78rem" }}>No active case loaded. Navigate to Investigations to select a dossier.</p>
            </div>
          )}
        </div>

        {/* Right: Unresolved Alerts & Live Telemetry Queue */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
          <div className="panel-header" style={{ marginBottom: "0.2rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <ShieldAlert size={16} style={{ color: "var(--color-high-risk)" }} />
              <h3 style={{ margin: 0, fontSize: "0.92rem", fontWeight: 700 }}>Priority Alert Queue</h3>
            </div>
            <button
              className="btn btn-secondary"
              style={{ fontSize: "0.7rem", padding: "2px 6px" }}
              onClick={() => onNavigate("investigation")}
            >
              All Alerts
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.45rem", overflowY: "auto", maxHeight: "360px" }}>
            {(fraudAlerts && fraudAlerts.length > 0) ? (
              fraudAlerts.slice(0, 6).map((alert, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    if (alert.case_id) onSelectCase(alert.case_id);
                    onNavigate("investigation");
                  }}
                  style={{
                    background: "rgba(8, 12, 22, 0.4)",
                    borderLeft: `3px solid ${alert.severity === "CRITICAL" ? "var(--color-critical)" : (alert.severity === "HIGH" ? "var(--color-high-risk)" : "var(--color-caution)")}`,
                    borderRadius: "0 var(--radius-md) var(--radius-md) 0",
                    padding: "0.55rem 0.75rem",
                    cursor: "pointer",
                    transition: "all 0.15s ease"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "0.76rem", fontWeight: 700, color: "var(--text-primary)" }}>
                      {alert.rule_name || alert.title || `Alert #${alert.id || idx + 1}`}
                    </span>
                    <span style={{ fontSize: "0.62rem", fontFamily: "JetBrains Mono", color: "var(--text-dim)" }}>
                      {alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : "Live"}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                    {alert.description || alert.reason || "Adversarial behavioral vector identified"}
                  </div>
                  {alert.case_id && (
                    <div style={{ fontSize: "0.65rem", color: "var(--brand-primary)", marginTop: "3px", fontFamily: "JetBrains Mono" }}>
                      CASE: {alert.case_id}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-dim)", fontSize: "0.75rem" }}>
                ✓ No critical alerts in uncontained state.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
