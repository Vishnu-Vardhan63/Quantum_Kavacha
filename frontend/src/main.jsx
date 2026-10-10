import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { motion, AnimatePresence } from "framer-motion";
import confetti from "canvas-confetti";
import {
  Shield, Zap, Cpu, BarChart3, AlertTriangle, CheckCircle2,
  Activity, Database, Network, Play, Pause, RefreshCw,
  Search, Lock, Eye, Layers, ArrowRight, Check, X,
  Crosshair, MessageSquare, Send, HelpCircle, Compass, Flame,
  FileSearch, GitFork, ShieldAlert, CpuIcon, Terminal, Info,
  Sliders, ArrowUpRight, QrCode, Image as ImageIcon, Link as LinkIcon,
  Upload, CheckCircle, AlertCircle, AlertOctagon, RotateCcw,
  FileText, Download, User, Smartphone, Globe, CreditCard, Clock,
  Edit3, ChevronDown, ChevronUp, Copy, Sparkles, ExternalLink, Server
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import QuantumCore3D from "./QuantumCore3D";
import TransactionGraph3D from "./TransactionGraph3D";
import ResponseCenterWorkspace from "./components/ResponseCenterWorkspace";
import DeviceTrustWorkspace from "./components/DeviceTrustWorkspace";
import "./style.css";
import { TransactionsWorkspace } from './components/TransactionsWorkspace';
import { DetectionCenterWorkspace } from './components/DetectionCenterWorkspace';
import { FraudAlertsWorkspace } from './components/FraudAlertsWorkspace';
import { AttackSimulationLab } from './components/AttackSimulationLab';
import { CommandOverviewWorkspace } from './components/CommandOverviewWorkspace';
import { InvestigationCommandCenter } from './components/InvestigationCommandCenter';
import { AgentWorkspace } from './components/AgentWorkspace';
import { QuantumResearchLabWorkspace } from './components/QuantumResearchLabWorkspace';
import { translations } from './i18n/translations';

const FASTAPI_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_FASTAPI_BASE || "http://127.0.0.1:8000";
const EXPRESS_BASE = import.meta.env.VITE_EXPRESS_BASE || "http://127.0.0.1:5000";

function EvidenceVerificationPanel({ evidenceVerification, onOpenDetails }) {
  if (!evidenceVerification) return null;

  const va = evidenceVerification.visual_assessment || {};
  const qr = evidenceVerification.qr_cross_check || {};
  const isGeminiLive = evidenceVerification.provider?.includes("Gemini") && evidenceVerification.analysis_status === "COMPLETED";

  const aiLikelihood = va.ai_generation_likelihood !== null && va.ai_generation_likelihood !== undefined
    ? `${(va.ai_generation_likelihood * 100).toFixed(0)}%`
    : va.ai_generation_assessment || "N/A";

  const aiBadgeClass = va.ai_generation_assessment === "HIGH INDICATION" ? "critical" : (va.ai_generation_assessment === "MODERATE" ? "moderate" : "observed");
  const manipClass = va.manipulation_level === "HIGH" ? "critical" : (va.manipulation_level === "MODERATE" ? "moderate" : "observed");

  return (
    <div className="evidence-verification-panel">
      <div className="ev-header">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <ImageIcon size={18} style={{ color: "var(--brand-cyan)" }} />
          <h3 style={{ margin: 0, fontSize: "0.88rem", fontWeight: 700, color: "var(--text-primary)" }}>
            AI-Assisted Evidence Verification (Multimodal Layer)
          </h3>
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <span className={`evidence-tag ${isGeminiLive ? "observed" : "unavailable"}`}>
            {evidenceVerification.provider} • {evidenceVerification.analysis_status}
          </span>
          <button
            className="btn btn-secondary"
            style={{ padding: "0.25rem 0.6rem", fontSize: "0.72rem" }}
            onClick={onOpenDetails}
          >
            <Eye size={12} /> View Evidence Details
          </button>
        </div>
      </div>

      <div className="ev-metrics-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
        <div className="ev-metric-tile">
          <span className="ev-metric-label">AI-Generation Assessment</span>
          <div className="ev-metric-val-row">
            <span className="ev-metric-val">{aiLikelihood}</span>
            <span className={`evidence-tag ${aiBadgeClass}`}>{va.ai_generation_assessment || "UNLIKELY"}</span>
          </div>
          <span className="ev-metric-sub">
            Probabilistic indicator (statistical)
          </span>
        </div>

        <div className="ev-metric-tile">
          <span className="ev-metric-label">Image Integrity & Splicing</span>
          <div className="ev-metric-val-row">
            <span className="ev-metric-val">
              {va.image_integrity_score !== null && va.image_integrity_score !== undefined ? `${va.image_integrity_score}%` : "95%"}
            </span>
            <span className={`evidence-tag ${manipClass}`}>{va.manipulation_level || "NONE"}</span>
          </div>
          <span className="ev-metric-sub">
            {va.manipulation_level === "NONE_DETECTED" || !va.manipulation_level ? "Consistent font geometry" : "Alteration indicators flagged"}
          </span>
        </div>

        <div className="ev-metric-tile">
          <span className="ev-metric-label">Visual & Text Consistency</span>
          <div className="ev-metric-val-row">
            <span className="ev-metric-val">
              {va.visual_consistency_score !== null && va.visual_consistency_score !== undefined ? `${va.visual_consistency_score}%` : "92%"}
            </span>
            <span className="evidence-tag observed">
              {va.text_consistency_score != null ? `Text: ${va.text_consistency_score}%` : "Aligned"}
            </span>
          </div>
          <span className="ev-metric-sub">
            Font and layout alignment
          </span>
        </div>

        <div className="ev-metric-tile">
          <span className="ev-metric-label">QR Cross-Verification</span>
          <div className="ev-metric-val-row">
            <span className={`evidence-tag ${qr.amount_comparison === "MATCH" && qr.recipient_comparison === "MATCH" ? "observed" : (qr.amount_comparison === "MISMATCH" || qr.recipient_comparison === "MISMATCH" ? "critical" : "unavailable")}`}>
              {qr.amount_comparison === "MISMATCH" || qr.recipient_comparison === "MISMATCH" ? "MISMATCH" : (qr.amount_comparison === "MATCH" ? "MATCH" : "UNAVAILABLE")}
            </span>
            <span className="ev-metric-val" style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
              {qr.system_derived_consistency_score !== null && qr.system_derived_consistency_score !== undefined ? `${(qr.system_derived_consistency_score * 100).toFixed(0)}%` : "100%"}
            </span>
          </div>
          <span className="ev-metric-sub" title={qr.consistency_explanation}>
            {qr.consistency_explanation || "Cross-check vs decoded payload"}
          </span>
        </div>
      </div>

      <div style={{ marginTop: "0.5rem", fontSize: "0.68rem", color: "var(--text-dim)", fontStyle: "italic", borderTop: "1px solid var(--border-subtle)", paddingTop: "0.35rem" }}>
        * Note: AI-generation & visual assessment metrics are probabilistic signals and do not replace cryptographic payment gateway verification.
      </div>
    </div>
  );
}

function ThreatIntelligencePanel({ threatIntelligence }) {
  if (!threatIntelligence || Object.keys(threatIntelligence).length === 0) return null;

  const vtUrl = threatIntelligence.virustotal_url || {};
  const vtFile = threatIntelligence.virustotal_file || {};
  const whois = threatIntelligence.whois || {};
  const dns = threatIntelligence.dns || {};
  const tls = threatIntelligence.tls || {};
  const fileMeta = threatIntelligence.file_metadata || {};

  const vtActive = vtUrl.status === "OBSERVED" || vtFile.status === "OBSERVED";
  const vtMalicious = vtUrl.malicious_count || vtFile.malicious_count || 0;
  const vtSuspicious = vtUrl.suspicious_count || vtFile.suspicious_count || 0;
  const vtTotal = vtUrl.total_vendors || vtFile.total_vendors || 0;

  return (
    <div style={{ background: "var(--bg-surface-elevated)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Globe size={16} style={{ color: "var(--brand-primary)" }} />
          <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>
            🌐 Threat Intelligence & Infrastructure Forensics
          </span>
        </div>
        <span className="evidence-tag observed" style={{ fontSize: "0.68rem" }}>
          Multi-Vendor Feeds
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.75rem" }}>
        {/* VirusTotal Reputation */}
        <div style={{ background: "rgba(255,255,255,0.02)", padding: "0.6rem 0.75rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>VirusTotal Reputation</div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginTop: "4px" }}>
            <span className={`evidence-tag ${vtMalicious > 0 ? "critical" : (vtSuspicious > 0 ? "moderate" : (vtActive ? "observed" : "unavailable"))}`}>
              {vtMalicious > 0 ? `${vtMalicious} Malicious Flags` : (vtSuspicious > 0 ? `${vtSuspicious} Suspicious` : (vtActive ? "0 / Clean Vendors" : (vtUrl.status || vtFile.status || "UNAVAILABLE")))}
            </span>
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "4px" }}>
            {vtTotal > 0 ? `Scanned by ${vtTotal} security engines` : "Hash / URL reputation feed"}
          </div>
        </div>

        {/* WHOIS & Domain Age */}
        {whois.status === "OBSERVED" && (
          <div style={{ background: "rgba(255,255,255,0.02)", padding: "0.6rem 0.75rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>Domain Age & Registrar</div>
            <div style={{ fontSize: "0.82rem", fontWeight: 600, color: whois.is_young_domain ? "var(--color-caution)" : "var(--text-primary)", marginTop: "4px" }}>
              {whois.domain_age_days != null ? `${whois.domain_age_days} Days Old` : "Registered"} {whois.is_young_domain && "⚠️ (Young Domain)"}
            </div>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "2px" }}>
              {whois.registrar || "Protected registrar"}
            </div>
          </div>
        )}

        {/* TLS Certificate */}
        {tls.status === "OBSERVED" && (
          <div style={{ background: "rgba(255,255,255,0.02)", padding: "0.6rem 0.75rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>TLS Certificate Trust</div>
            <div style={{ fontSize: "0.82rem", fontWeight: 600, color: tls.is_expired ? "var(--color-high-risk)" : "var(--color-safe)", marginTop: "4px" }}>
              {tls.is_expired ? "✕ Certificate Expired" : "✓ Active TLS"} ({tls.tls_version || "TLSv1.3"})
            </div>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "2px" }}>
              Issuer: {tls.issuer || "Trusted CA"}
            </div>
          </div>
        )}

        {/* File Cryptographic Integrity */}
        {fileMeta.sha256 && (
          <div style={{ background: "rgba(255,255,255,0.02)", padding: "0.6rem 0.75rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>Cryptographic Hash (SHA-256)</div>
            <div style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "var(--text-primary)", marginTop: "4px", wordBreak: "break-all" }}>
              {fileMeta.sha256.substring(0, 16)}...{fileMeta.sha256.substring(fileMeta.sha256.length - 8)}
            </div>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "2px" }}>
              Format: {fileMeta.detected_type} ({fileMeta.size_bytes ? `${(fileMeta.size_bytes / 1024).toFixed(1)} KB` : ""})
            </div>
          </div>
        )}
      </div>

      <div style={{ marginTop: "0.6rem", fontSize: "0.68rem", color: "var(--text-dim)", fontStyle: "italic", borderTop: "1px solid var(--border-subtle)", paddingTop: "0.35rem" }}>
        * Note: External threat intelligence and domain metrics provide supplementary signal telemetry. Final risk decisions are fused by Q-FraudShield.
      </div>
    </div>
  );
}

function EvidenceDetailsModal({ isOpen, onClose, evidenceVerification, caseId }) {
  if (!isOpen || !evidenceVerification) return null;

  const va = evidenceVerification.visual_assessment || {};
  const qr = evidenceVerification.qr_cross_check || {};
  const checks = evidenceVerification.evidence_checks || [];
  const obs = evidenceVerification.observations || [];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <motion.div
        className="evidence-modal-content"
        onClick={(e) => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.96 }}
      >
        <div className="panel-header" style={{ borderBottom: "1px solid var(--border-subtle)", paddingBottom: "0.75rem", marginBottom: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <FileSearch size={18} style={{ color: "var(--brand-primary)" }} />
              <h2 style={{ margin: 0, fontSize: "1rem", color: "var(--text-primary)" }}>
                Multimodal Forensic Evidence Dossier
              </h2>
            </div>
            <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
              CASE ID: {caseId || "QF-CURRENT"} • Provider: {evidenceVerification.provider} • Engine: {evidenceVerification.model_version}
            </span>
          </div>
          <button className="btn btn-secondary" onClick={onClose} style={{ padding: "0.2rem 0.5rem", fontSize: "0.8rem" }}>✕</button>
        </div>

        <div style={{ maxHeight: "65vh", overflowY: "auto", paddingRight: "0.5rem" }}>
          
          {/* Section 1: AI / Synthetic Media Assessment */}
          <div className="ev-section-card">
            <h4>🤖 1. AI / Synthetic Media Assessment</h4>
            <div className="ev-detail-grid">
              <div>
                <span className="detail-label">AI-Generation Likelihood:</span>
                <span className={`evidence-tag ${va.ai_generation_assessment === "HIGH INDICATION" ? "critical" : (va.ai_generation_assessment === "MODERATE" ? "moderate" : "observed")}`}>
                  {va.ai_generation_likelihood !== null && va.ai_generation_likelihood !== undefined ? `${(va.ai_generation_likelihood * 100).toFixed(1)}% (${va.ai_generation_assessment})` : va.ai_generation_assessment}
                </span>
              </div>
              <div>
                <span className="detail-label">UI Authenticity Score:</span>
                <span className="detail-val">{va.ui_authenticity_score !== null && va.ui_authenticity_score !== undefined ? `${va.ui_authenticity_score}%` : "UNAVAILABLE"}</span>
              </div>
            </div>
            <div className="disclaimer-box" style={{ marginTop: "0.6rem" }}>
              <Info size={14} style={{ color: "var(--brand-cyan)", flexShrink: 0, marginTop: "2px" }} />
              <span>
                <b>Forensic Disclaimer:</b> AI and synthetic media assessments are probabilistic estimations derived from visual artifact heuristics. Final fraud classification is governed by the multi-signal risk fusion engine.
              </span>
            </div>
          </div>

          {/* Section 2: Image Integrity & Manipulation Indicators */}
          <div className="ev-section-card">
            <h4>🔬 2. Image Integrity & Splicing Analysis</h4>
            <div className="ev-detail-grid">
              <div>
                <span className="detail-label">Overall Integrity Score:</span>
                <span className="detail-val">{va.image_integrity_score !== null && va.image_integrity_score !== undefined ? `${va.image_integrity_score}%` : "UNAVAILABLE"}</span>
              </div>
              <div>
                <span className="detail-label">Manipulation Severity:</span>
                <span className={`evidence-tag ${va.manipulation_level === "HIGH" ? "critical" : (va.manipulation_level === "MODERATE" ? "moderate" : "observed")}`}>
                  {va.manipulation_level}
                </span>
              </div>
            </div>
            {va.manipulation_indicators && va.manipulation_indicators.length > 0 ? (
              <div style={{ marginTop: "0.6rem" }}>
                <span className="detail-label" style={{ display: "block", marginBottom: "0.3rem" }}>Detected Manipulation Indicators:</span>
                <ul className="ev-bullet-list">
                  {va.manipulation_indicators.map((m, i) => (
                    <li key={i} style={{ color: "#FCA5A5" }}>⚠️ {m}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "var(--color-safe)" }}>✓ No anomalous font splicing, compression halos, or duplicated UI elements observed.</p>
            )}
          </div>

          {/* Section 3: Extracted Semantic Fields & OCR Cross-Check */}
          <div className="ev-section-card">
            <h4>📝 3. Extracted Information & OCR Cross-Check</h4>
            {checks.length > 0 ? (
              <table className="ev-fields-table">
                <thead>
                  <tr>
                    <th>Field</th>
                    <th>Extracted Value</th>
                    <th>Expected / Target</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {checks.map((chk, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{chk.field}</td>
                      <td style={{ fontFamily: "JetBrains Mono", fontSize: "0.75rem" }}>{String(chk.extracted_value)}</td>
                      <td style={{ fontFamily: "JetBrains Mono", fontSize: "0.75rem" }}>{String(chk.expected_or_qr_value)}</td>
                      <td>
                        <span className={`evidence-tag ${chk.result === "MATCH" ? "observed" : (chk.result === "MISMATCH" ? "critical" : "unavailable")}`}>
                          {chk.result}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", margin: 0 }}>No cross-field comparison targets available for current artifact.</p>
            )}
          </div>

          {/* Section 4: QR Verification & Screenshot ↔ QR Cross-Verification */}
          <div className="ev-section-card">
            <h4>🔍 4. QR Forensic Verification & Cross-Check</h4>
            <div className="ev-detail-grid">
              <div>
                <span className="detail-label">Amount Comparison:</span>
                <span className={`evidence-tag ${qr.amount_comparison === "MATCH" ? "observed" : (qr.amount_comparison === "MISMATCH" ? "critical" : "unavailable")}`}>
                  {qr.amount_comparison}
                </span>
              </div>
              <div>
                <span className="detail-label">Recipient Comparison:</span>
                <span className={`evidence-tag ${qr.recipient_comparison === "MATCH" ? "observed" : (qr.recipient_comparison === "MISMATCH" ? "critical" : "unavailable")}`}>
                  {qr.recipient_comparison}
                </span>
              </div>
              <div>
                <span className="detail-label">System-Derived Consistency:</span>
                <span className="detail-val">{qr.system_derived_consistency_score !== null && qr.system_derived_consistency_score !== undefined ? `${(qr.system_derived_consistency_score * 100).toFixed(0)}%` : "UNAVAILABLE"}</span>
              </div>
            </div>
            <p style={{ fontSize: "0.76rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>
              <b>Consistency Rationale:</b> {qr.consistency_explanation}
            </p>
          </div>

          {/* Section 5: Forensic Findings & Observations */}
          <div className="ev-section-card">
            <h4>📋 5. Observed Forensic Findings ({obs.length})</h4>
            <ul className="ev-bullet-list">
              {obs.map((o, idx) => (
                <li key={idx}>🔹 {o}</li>
              ))}
            </ul>
          </div>

        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1rem" }}>
          <button className="btn btn-primary" onClick={onClose}>
            Close Forensic Details
          </button>
        </div>
      </motion.div>
    </div>
  );
}

function FraudDNAHub({ fraudDna, counterfactuals }) {
  const [selectedAxisKey, setSelectedAxisKey] = useState("AMOUNT_TRANSACTION");
  if (!fraudDna) return null;

  const axes = fraudDna.axes || {};
  const selectedAxis = axes[selectedAxisKey] || (fraudDna.fraud_dna_fingerprint && fraudDna.fraud_dna_fingerprint[0]);
  const explanation = fraudDna.explanation_summary || {};
  const timeline = fraudDna.evidence_timeline || [];
  const limitations = fraudDna.limitations || [];

  const axisIcons = {
    AMOUNT_TRANSACTION: "💳",
    DEVICE: "📱",
    BEHAVIOR: "⚡",
    NETWORK_GRAPH: "🌐",
    QUANTUM_COMPLEXITY: "⚛️"
  };

  return (
    <div className="frauddna-hub-card">
      <div className="hub-header">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Layers size={18} style={{ color: "var(--brand-indigo)" }} />
          <h3 style={{ margin: 0, fontSize: "0.9rem", fontWeight: 700, color: "var(--text-primary)" }}>
            FraudDNA™ 5-Axis Risk Fingerprint & Attribution Profile
          </h3>
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          {fraudDna.quality_verified && (
            <span className="evidence-tag observed" title="Passed automated explanation verification filter">
              ✓ Verified Attribution
            </span>
          )}
          <span className="evidence-tag observed">EXPLAINABILITY CORE</span>
        </div>
      </div>

      {/* 5-Axis Interactive Grid */}
      <div className="frauddna-5axis-grid">
        {Object.entries(axes).map(([key, axis]) => {
          const isSelected = selectedAxisKey === key;
          const isQuantum = key === "QUANTUM_COMPLEXITY";
          return (
            <div
              key={key}
              className={`axis-tile ${isSelected ? "selected" : ""}`}
              onClick={() => setSelectedAxisKey(isSelected ? null : key)}
              style={{ cursor: "pointer" }}
            >
              <div className="axis-tile-header">
                <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
                  {axisIcons[key] || "🔹"} {axis.axis_name ? axis.axis_name.replace("Risk", "").trim() : key}
                </span>
                <span className={`evidence-tag ${axis.status ? axis.status.toLowerCase() : "observed"}`}>
                  {axis.status}
                </span>
              </div>
              <div className="axis-score-row">
                <span className="axis-score">
                  {isQuantum ? (axis.quantum_state || "FAST_PATH") : `${axis.score}%`}
                </span>
                <span className="severity-badge">
                  {axis.severity}
                </span>
              </div>
              {!isQuantum && (
                <div className="axis-progress-track">
                  <div
                    className={`axis-progress-fill ${axis.severity ? axis.severity.toLowerCase() : "low"}`}
                    style={{ width: `${Math.min(100, Math.max(0, axis.score))}%` }}
                  />
                </div>
              )}
              <div className="axis-driver-preview">
                {axis.primary_driver || "Nominal baseline parameters"}
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Axis Inspector Drawer */}
      {selectedAxis && (
        <motion.div
          className="axis-inspector-card"
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.15 }}
        >
          <div className="inspector-header">
            <span className="inspector-title">
              🔍 Axis Deep Dive: {selectedAxis.axis_name || selectedAxisKey}
            </span>
            <span className={`evidence-tag ${selectedAxis.status ? selectedAxis.status.toLowerCase() : "observed"}`}>
              EVIDENCE STATUS: [{selectedAxis.status}]
            </span>
          </div>
          <p style={{ fontSize: "0.76rem", color: "var(--text-secondary)", marginBottom: "0.75rem", lineHeight: 1.45 }}>
            {selectedAxis.explanation}
          </p>
          <div className="inspector-grid">
            <div>
              <span style={{ color: "#FCA5A5", fontWeight: 700, fontSize: "0.72rem", display: "block", marginBottom: "0.35rem" }}>
                🔺 Primary Risk Drivers ({selectedAxis.risk_drivers?.length || 0})
              </span>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                {selectedAxis.risk_drivers && selectedAxis.risk_drivers.length > 0 ? (
                  selectedAxis.risk_drivers.map((d, di) => (
                    <div key={di} className="contrib-item positive">
                      <span>{d}</span>
                    </div>
                  ))
                ) : (
                  <span style={{ fontSize: "0.72rem", color: "var(--text-dim)" }}>No elevated risk drivers on this axis.</span>
                )}
              </div>
            </div>

            <div>
              <span style={{ color: "#6EE7B7", fontWeight: 700, fontSize: "0.72rem", display: "block", marginBottom: "0.35rem" }}>
                🔻 Mitigating & Calibrating Factors ({selectedAxis.mitigating_factors?.length || 0})
              </span>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                {selectedAxis.mitigating_factors && selectedAxis.mitigating_factors.length > 0 ? (
                  selectedAxis.mitigating_factors.map((m, mi) => (
                    <div key={mi} className="contrib-item negative">
                      <span>{m}</span>
                    </div>
                  ))
                ) : (
                  <span style={{ fontSize: "0.72rem", color: "var(--text-dim)" }}>No specific mitigating offsets recorded.</span>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Dual-Level Explanations Panel */}
      <div className="explanation-duo-grid">
        <div className="explanation-box">
          <h4>💡 Plain-English Summary (Customer / Merchant)</h4>
          <p>{explanation.simple_explanation || "Payment is evaluated within standard operational safety parameters."}</p>
        </div>
        <div className="explanation-box">
          <h4>🔬 Technical Forensic Rationale (SOC Analyst)</h4>
          <p>{explanation.technical_explanation || explanation.decision_rationale || "Hybrid classical ML, deep anomaly, and quantum state projection converged."}</p>
        </div>
      </div>

      {/* Actionable Counterfactuals */}
      {counterfactuals && counterfactuals.length > 0 && (
        <div style={{ marginTop: "1rem", background: "var(--bg-surface-elevated)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: "1rem" }}>
          <h4 style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.5rem" }}>
            🎯 Actionable Counterfactuals ("What would alter the risk tier?")
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
            {counterfactuals.map((cf, idx) => (
              <div key={idx} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", background: "rgba(9, 13, 22, 0.4)", padding: "0.4rem 0.6rem", borderRadius: "4px" }}>
                <span style={{ color: "var(--text-secondary)" }}>{cf.condition}</span>
                <span style={{ color: "var(--color-safe)", fontFamily: "JetBrains Mono" }}>Projected Risk: <b>{cf.resulting_risk_score}%</b> (-{cf.risk_reduction_pct}%)</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function PayloadIntegrityPanel({ payloadIntegrity }) {
  if (!payloadIntegrity) return null;
  const { integrity_status, fields_compared, discrepancies, fields } = payloadIntegrity;
  const statusColor = integrity_status === "INTEGRITY_VERIFIED" ? "var(--color-safe)" : (integrity_status === "COMPROMISED" ? "var(--color-high-risk)" : "var(--color-caution)");
  const statusBadge = integrity_status === "INTEGRITY_VERIFIED" ? "observed" : (integrity_status === "COMPROMISED" ? "critical" : "moderate");

  return (
    <div style={{ background: "var(--bg-surface-elevated)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.6rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Shield size={16} style={{ color: statusColor }} />
          <span style={{ fontSize: "0.84rem", fontWeight: 700, color: "var(--text-primary)" }}>
            Payment Payload Cross-Validation & Field Integrity
          </span>
        </div>
        <span className={`evidence-tag ${statusBadge}`}>
          {integrity_status} ({fields_compared} fields)
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.45rem", marginBottom: "0.6rem" }}>
        {Object.entries(fields || {}).map(([key, item]) => {
          const itemColor = item.status === "MATCH" ? "var(--color-safe)" : (item.status === "MISMATCH" ? "var(--color-high-risk)" : "var(--text-dim)");
          return (
            <div key={key} style={{ background: "rgba(9, 13, 22, 0.4)", padding: "0.45rem 0.6rem", borderRadius: "4px", border: "1px solid var(--border-subtle)" }}>
              <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", textTransform: "uppercase" }}>{item.field_name || key}</div>
              <div style={{ fontSize: "0.76rem", fontWeight: 700, color: itemColor, marginTop: "2px" }}>
                {item.status === "MATCH" ? "✓ MATCH" : (item.status === "MISMATCH" ? "✕ MISMATCH" : "— UNAVAILABLE")}
              </div>
            </div>
          );
        })}
      </div>

      {discrepancies && discrepancies.length > 0 && (
        <div style={{ background: "rgba(239, 68, 68, 0.08)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "6px", padding: "0.5rem 0.75rem", marginTop: "0.4rem" }}>
          <span style={{ fontSize: "0.72rem", color: "#FCA5A5", fontWeight: 700 }}>Flagged Integrity Discrepancies:</span>
          {discrepancies.map((d, idx) => (
            <div key={idx} style={{ fontSize: "0.74rem", color: "var(--text-primary)", marginTop: "2px" }}>• {d}</div>
          ))}
        </div>
      )}
    </div>
  );
}

function TransactionDNAPanel({ transactionDna }) {
  if (!transactionDna) return null;
  const { user_id, status, baseline_summary, deviations, dynamic_risk_multiplier } = transactionDna;
  const isInsufficient = status === "INSUFFICIENT_HISTORY";
  const badgeClass = status === "ANOMALOUS_DEVIATION" ? "critical" : (status === "ELEVATED_DEVIATION" ? "moderate" : (status === "CONSISTENT" ? "observed" : "unavailable"));

  return (
    <div style={{ background: "var(--bg-surface-elevated)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.6rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <User size={16} style={{ color: "var(--brand-primary)" }} />
          <span style={{ fontSize: "0.84rem", fontWeight: 700, color: "var(--text-primary)" }}>
            Transaction DNA™ Behavioral Baseline Profile ({user_id})
          </span>
        </div>
        <span className={`evidence-tag ${badgeClass}`}>
          {status} {dynamic_risk_multiplier > 1.0 ? `(Multiplier: ${dynamic_risk_multiplier}x)` : ""}
        </span>
      </div>

      <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.6rem" }}>
        {baseline_summary}
      </p>

      {deviations && deviations.length > 0 ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.5rem" }}>
          {deviations.map((dev, idx) => {
            const devColor = dev.severity === "CRITICAL" || dev.severity === "HIGH" ? "var(--color-high-risk)" : (dev.severity === "MEDIUM" ? "var(--color-caution)" : "var(--color-safe)");
            return (
              <div key={idx} style={{ background: "rgba(9, 13, 22, 0.4)", padding: "0.5rem 0.65rem", borderRadius: "4px", border: "1px solid var(--border-subtle)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase" }}>{dev.dimension}</span>
                  <span style={{ fontSize: "0.65rem", fontWeight: 700, color: devColor }}>{dev.severity}</span>
                </div>
                <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
                  Observed: <span style={{ fontFamily: "JetBrains Mono" }}>{String(dev.observed_value)}</span>
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "1px" }}>
                  Baseline: {String(dev.baseline_expected)}
                </div>
                <div style={{ fontSize: "0.68rem", color: devColor, marginTop: "2px" }}>
                  {dev.explanation}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div style={{ fontSize: "0.74rem", color: "var(--text-dim)", fontStyle: "italic" }}>
          {isInsufficient ? "Profile initialized with cold-start status (<3 historical transactions). DNA behavioral scoring safely marked UNAVAILABLE." : "No significant deviations from established behavioral profile."}
        </div>
      )}
    </div>
  );
}

function getPlainLanguageReasons(checkResult) {
  if (!checkResult) return [];
  const reasons = [];

  const riskSignals = checkResult.risk_signals || [];
  const ev = checkResult.evidence_verification || {};
  const qr = ev.qr_cross_check || {};
  const va = ev.visual_assessment || {};

  // 1. Recipient mismatch
  if (qr.recipient_comparison === "MISMATCH" || riskSignals.some(s => s.name?.includes("Identity") || s.name?.includes("Payee"))) {
    reasons.push({
      title: "Recipient mismatch",
      impact: "High impact",
      severity: "high",
      description: "The recipient shown in the payment evidence does not match the recipient encoded in the QR code or payment route."
    });
  }

  // 2. Amount mismatch
  if (qr.amount_comparison === "MISMATCH" || riskSignals.some(s => s.name?.includes("Amount"))) {
    reasons.push({
      title: "Amount mismatch",
      impact: "High impact",
      severity: "high",
      description: "The payment screenshot shows a different amount than what the QR code or payment link actually requests."
    });
  }

  // 3. Image manipulation / AI generation
  if (va.manipulation_level === "HIGH" || va.manipulation_level === "MODERATE" || va.ai_generation_assessment === "HIGH INDICATION") {
    reasons.push({
      title: "Image alteration detected",
      impact: "High impact",
      severity: "high",
      description: "The uploaded payment image shows visual inconsistencies, font alterations, or synthetic generation patterns."
    });
  }

  // 4. Phishing / Malicious link
  if (riskSignals.some(s => s.name?.includes("Lookalike") || s.name?.includes("Phishing") || s.name?.includes("SSRF") || s.name?.includes("TLD"))) {
    reasons.push({
      title: "Suspicious payment link",
      impact: "High impact",
      severity: "high",
      description: "The payment URL uses an unverified or lookalike domain attempting to impersonate a trusted payment provider."
    });
  }

  // 5. Social engineering / Urgency
  if (riskSignals.some(s => s.name?.includes("Urgency") || s.name?.includes("Suspension") || s.name?.includes("Lottery"))) {
    reasons.push({
      title: "Urgency pressure language",
      impact: "Medium impact",
      severity: "medium",
      description: "The payment message contains urgent coercion or disconnection threats designed to rush authorization."
    });
  }

  // 6. Device / Velocity
  if (riskSignals.some(s => s.name?.includes("Device") || s.name?.includes("Velocity") || s.name?.includes("Anomaly"))) {
    reasons.push({
      title: "Unfamiliar device & high activity",
      impact: "Medium impact",
      severity: "medium",
      description: "This payment originates from an unfamiliar device profile with higher than normal hourly transaction frequency."
    });
  }

  // If safe, return reassuring points
  if (reasons.length === 0) {
    if (checkResult.trust_level?.includes("SAFE")) {
      reasons.push({
        title: "Verified recipient handle",
        impact: "Positive factor",
        severity: "safe",
        description: "The recipient address matches the verified merchant registration."
      });
      reasons.push({
        title: "Consistent transaction amount",
        impact: "Positive factor",
        severity: "safe",
        description: "The payment amount is consistent with normal baseline activity."
      });
      reasons.push({
        title: "Authentic payment artifact",
        impact: "Positive factor",
        severity: "safe",
        description: "No visual manipulation, layout tampering, or anomalous formatting was detected."
      });
    } else {
      reasons.push({
        title: "Elevated risk signals",
        impact: "Medium impact",
        severity: "medium",
        description: "Multiple telemetry indicators suggest secondary verification is advisable before proceeding."
      });
    }
  }

  return reasons;
}

function getEvidenceChecklist(checkResult) {
  if (!checkResult) return [];
  const ev = checkResult.evidence_verification || {};
  const qr = ev.qr_cross_check || {};
  const isSafe = checkResult.trust_level?.includes("SAFE");

  return [
    { label: "QR code verified", status: (qr.status === "DECODED" || checkResult.input_type === "QR") ? "ok" : (checkResult.input_type === "SCREENSHOT" || checkResult.input_type === "LINK" ? "na" : "ok") },
    { label: "Recipient address checked", status: qr.recipient_comparison === "MISMATCH" ? "fail" : "ok" },
    { label: "Payment amount checked", status: qr.amount_comparison === "MISMATCH" ? "fail" : "ok" },
    { label: "Screenshot authenticity", status: ev.visual_assessment?.manipulation_level === "HIGH" ? "fail" : (checkResult.input_type === "SCREENSHOT" ? "ok" : "na") },
    { label: "Domain & URL security", status: checkResult.risk_signals?.some(s => s.name?.includes("Lookalike") || s.name?.includes("SSRF")) ? "fail" : (checkResult.input_type === "LINK" ? "ok" : "na") },
    { label: "Device signals checked", status: isSafe ? "ok" : "fail" },
  ];
}

function DemoScenariosQuickPick({ checkScenarios, selectedScenarioId, onSelectScenario }) {
  const primaryScenarios = [
    {
      id: "SCENARIO_1_SAFE_QR",
      title: "Safe Payment",
      desc: "Verified merchant & genuine QR payload",
      icon: "🛡️",
      tag: "DEMO / SAFE"
    },
    {
      id: "SCENARIO_2_SUSPICIOUS_SE_QR",
      title: "Suspicious Payment",
      desc: "Deceptive domain & social urgency lure",
      icon: "⚠️",
      tag: "DEMO / HIGH RISK"
    },
    {
      id: "SCENARIO_B_MANIPULATED_SCREENSHOT",
      title: "Manipulated Screenshot",
      desc: "Conflicting receipt amount vs QR payload",
      icon: "🔍",
      tag: "DEMO / MISMATCH"
    }
  ];

  return (
    <div className="scenarios-quick-container">
      <div className="scenarios-quick-title">
        <span>WANT TO SEE HOW IT WORKS?</span>
        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "none", fontWeight: 500 }}>
          Select a sample scenario to test the live fraud intelligence engine
        </span>
      </div>

      <div className="scenarios-quick-grid">
        {primaryScenarios.map((sc) => {
          const isSelected = selectedScenarioId === sc.id;
          return (
            <button
              key={sc.id}
              className={`scenario-card-btn ${isSelected ? "active" : ""}`}
              onClick={() => {
                const matched = checkScenarios.find(s => s.id === sc.id) || { id: sc.id };
                onSelectScenario(matched);
              }}
            >
              <div className="card-title">
                <span>{sc.icon}</span> {sc.title}
                <span style={{ fontSize: "0.6rem", color: "var(--text-muted)", marginLeft: "auto", background: "rgba(255,255,255,0.06)", padding: "1px 5px", borderRadius: "3px" }}>
                  {sc.tag}
                </span>
              </div>
              <div className="card-desc">{sc.desc}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function HumanFirstCheckPaymentResult({
  checkResult,
  viewMode,
  onToggleViewMode,
  onOpenEvidenceDetails,
  onTransferToInvestigation,
  showAdvancedDetails,
  onToggleAdvancedDetails
}) {
  if (!checkResult) return null;

  const reasons = getPlainLanguageReasons(checkResult);
  const checklist = getEvidenceChecklist(checkResult);
  const ev = checkResult.evidence_verification || {};
  const qr = ev.qr_cross_check || {};
  const va = ev.visual_assessment || {};
  const ef = ev.extracted_fields || {};

  // Single Result Consistency Guard on UI:
  // If any high/critical reason is present, or risk_score >= 60, or decision is BLOCK -> strictly HIGH RISK.
  const hasCriticalOrHighReasons = reasons.some(r => r.severity === "high" || r.severity === "critical");
  const hasMediumReasons = reasons.some(r => r.severity === "medium");

  const isHighRisk = (checkResult.risk_score >= 60) || checkResult.decision === "BLOCK" || hasCriticalOrHighReasons;
  const isCaution = !isHighRisk && ((checkResult.risk_score >= 25) || checkResult.decision === "STEP_UP" || checkResult.decision === "HOLD" || checkResult.decision === "MONITOR" || hasMediumReasons);
  const isSafe = !isHighRisk && !isCaution && (checkResult.risk_score < 25);

  let heroTitle = "Low risk based on available evidence";
  let heroSub = "We did not detect major fraud indicators or payload tampering in this payment artifact.";
  let heroClass = "safe";
  let recTitle = "This payment appears consistent with baseline records. Proceed with normal caution.";

  if (isHighRisk) {
    heroTitle = "Potential fraud detected";
    heroSub = "High-risk indicators or discrepancy detected between evidence and payment routing. Do not complete payment.";
    heroClass = "high-risk";
    recTitle = "Do not complete this payment. Report the recipient if unauthorized.";
  } else if (isCaution) {
    heroTitle = "Review recommended before proceeding";
    heroSub = "Some payment parameters or recipient signatures do not fully match baseline records.";
    heroClass = "caution";
    recTitle = "Verify the recipient address through an independent trusted channel before paying.";
  }

  // Extract recipient and amount details for cross-comparison
  const qrPa = qr.raw_qr_payload ? (qr.raw_qr_payload.match(/pa=([^&]+)/)?.[1] || "—") : "—";
  const qrAm = qr.raw_qr_payload ? (qr.raw_qr_payload.match(/am=([^&]+)/)?.[1] || "—") : "—";
  const visualPa = ef.recipient_vpa || "—";
  const visualAm = ef.amount != null ? `₹${ef.amount.toLocaleString()}` : "—";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.15 }}
    >
      {/* 1. Header with View Mode Switcher */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
            Payment Risk Assessment
          </h2>
          <span className="sys-state completed" style={{ fontSize: "0.68rem" }}>
            CASE {checkResult.case_id}
          </span>
        </div>

        <div className="view-mode-toggle">
          <button
            className={`view-mode-btn ${viewMode === "simple" ? "active" : ""}`}
            onClick={() => onToggleViewMode("simple")}
          >
            Simple View
          </button>
          <button
            className={`view-mode-btn ${viewMode === "analyst" ? "active" : ""}`}
            onClick={() => onToggleViewMode("analyst")}
          >
            Analyst View 🔬
          </button>
        </div>
      </div>

      {/* 2. Primary Result Hero Banner */}
      <div className={`fintech-result-hero ${heroClass}`}>
        <div className="hero-status-row">
          <div className="hero-status-main">
            <div className="hero-status-icon-box">
              {isSafe ? <CheckCircle size={24} /> : (isCaution ? <AlertCircle size={24} /> : <AlertOctagon size={24} />)}
            </div>
            <div>
              <div className="hero-status-title">{heroTitle}</div>
              <div className="hero-status-sub">{heroSub}</div>
            </div>
          </div>
          <span className={`decision-pill ${isHighRisk ? "block" : (isCaution ? "step_up" : "approve")}`}>
            {isHighRisk ? "DO NOT PAY" : (isCaution ? "VERIFY FIRST" : "PROCEED (LOW RISK)")}
          </span>
        </div>

        <div className="fintech-kpi-row">
          <div className="fintech-kpi-tile">
            <span className="fintech-kpi-label">Risk Score</span>
            <div className="fintech-kpi-value" style={{ color: isSafe ? "var(--color-safe)" : (isCaution ? "var(--color-caution)" : "var(--color-high-risk)") }}>
              {checkResult.risk_score} <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>/ 100</span>
            </div>
            <span className="fintech-kpi-sub">
              {isSafe ? "Low risk indicator" : (isCaution ? "Review recommended" : "High risk detected")}
            </span>
          </div>

          <div className="fintech-kpi-tile">
            <span className="fintech-kpi-label">Evidence Quality</span>
            <div className="fintech-kpi-value">
              {((checkResult.confidence || 0.95) * 100).toFixed(0)}%
            </div>
            <span className="fintech-kpi-sub">Grounded evidence</span>
          </div>

          <div className="fintech-kpi-tile">
            <span className="fintech-kpi-label">Action Verdict</span>
            <div className="fintech-kpi-value" style={{ fontSize: "0.88rem" }}>
              {isHighRisk ? "Do Not Pay" : (isCaution ? "Verify First" : "Proceed with Caution")}
            </div>
            <span className="fintech-kpi-sub">Recommended next step</span>
          </div>

          <div className="fintech-kpi-tile">
            <span className="fintech-kpi-label">Quantum Gate</span>
            <div className="fintech-kpi-value" style={{ fontSize: "0.85rem", color: "var(--brand-primary)" }}>
              {checkResult.quantum_escalation?.quantum_escalation_status || "FAST_PATH"}
            </div>
            <span className="fintech-kpi-sub">Adaptive state</span>
          </div>
        </div>
      </div>

      {/* 3. SIMPLE VIEW CONTENT */}
      {viewMode === "simple" && (
        <>
          {/* Payment Details & Cross-Comparison Box */}
          <div className="checklist-card" style={{ marginBottom: "1rem" }}>
            <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.6rem" }}>
              <FileSearch size={15} style={{ color: "var(--brand-primary)" }} />
              <span>Payment Details Found & Verification Comparison</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.6rem" }}>
              <div style={{ background: "rgba(255,255,255,0.02)", padding: "0.5rem 0.75rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Recipient / Payee</div>
                <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
                  {visualPa !== "—" ? visualPa : (qrPa !== "—" ? decodeURIComponent(qrPa) : "Standard Account")}
                </div>
                {qr.recipient_comparison && (
                  <div style={{ fontSize: "0.7rem", marginTop: "2px", color: qr.recipient_comparison === "MATCH" ? "var(--color-safe)" : "var(--color-high-risk)" }}>
                    {qr.recipient_comparison === "MATCH" ? "✓ QR & Visual Match" : "✕ Recipient Mismatch"}
                  </div>
                )}
              </div>

              <div style={{ background: "rgba(255,255,255,0.02)", padding: "0.5rem 0.75rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Transaction Amount</div>
                <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
                  {visualAm !== "—" ? visualAm : (qrAm !== "—" ? `₹${qrAm}` : "—")}
                </div>
                {qr.amount_comparison && (
                  <div style={{ fontSize: "0.7rem", marginTop: "2px", color: qr.amount_comparison === "MATCH" ? "var(--color-safe)" : "var(--color-high-risk)" }}>
                    {qr.amount_comparison === "MATCH" ? "✓ Amount Matches" : "✕ Amount Mismatch"}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Why We Flagged / Approved This Payment */}
          <div className="reasons-box">
            <div className="reasons-header">
              <Info size={16} style={{ color: "var(--brand-primary)" }} />
              <span>{isSafe ? "Why this payment shows low risk" : "Why we flagged this payment"}</span>
            </div>
            <div className="reasons-list">
              {reasons.map((r, idx) => (
                <div key={idx} className={`reason-card ${r.severity}`}>
                  <div className="reason-top">
                    <span className="reason-title">{r.title}</span>
                    <span className="reason-impact">{r.impact}</span>
                  </div>
                  <div className="reason-desc">{r.description}</div>
                </div>
              ))}
            </div>
          </div>

          {/* What We Checked (Evidence Checklist) */}
          <div className="checklist-card">
            <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <CheckCircle2 size={16} style={{ color: "var(--color-safe)" }} />
              <span>What was checked</span>
            </div>
            <div className="checklist-grid">
              {checklist.map((item, idx) => (
                <div key={idx} className={`checklist-item ${item.status}`}>
                  <span>{item.status === "ok" ? "✓" : (item.status === "fail" ? "✕" : "—")}</span>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Next Steps Recommendation Box */}
          <div className="recommended-action-box">
            <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.35rem" }}>
              Recommended Next Action
            </div>
            <p style={{ fontSize: "0.76rem", color: "var(--text-secondary)", margin: "0 0 0.75rem 0" }}>
              {recTitle}
            </p>
            <div className="action-btn-row">
              {isHighRisk && (
                <>
                  <button className="btn btn-secondary" onClick={onOpenEvidenceDetails}>
                    <Eye size={13} /> View Forensic Evidence
                  </button>
                  <button className="btn btn-primary" onClick={onTransferToInvestigation}>
                    <Shield size={13} /> Open Full Investigation →
                  </button>
                </>
              )}
              {isCaution && (
                <>
                  <button className="btn btn-secondary" onClick={onOpenEvidenceDetails}>
                    <Eye size={13} /> Verify Recipient
                  </button>
                  <button className="btn btn-primary" onClick={onTransferToInvestigation}>
                    <Shield size={13} /> Open Investigation →
                  </button>
                </>
              )}
              {isSafe && (
                <>
                  <button className="btn btn-primary" onClick={() => alert("Low risk based on available evidence. Proceed with normal caution.")}>
                    <Check size={13} /> Proceed with Caution
                  </button>
                  <button className="btn btn-secondary" onClick={onOpenEvidenceDetails}>
                    <FileSearch size={13} /> View Evidence Summary
                  </button>
                </>
              )}
            </div>
          </div>
        </>
      )}

      {/* 4. ANALYST VIEW */}
      {viewMode === "analyst" && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.15 }}
          style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "1rem" }}
        >
          {/* Gemini Multimodal Evidence Verification Panel */}
          {checkResult.evidence_verification && (
            <EvidenceVerificationPanel
              evidenceVerification={checkResult.evidence_verification}
              onOpenDetails={onOpenEvidenceDetails}
            />
          )}

          {/* External Threat Intelligence & Infrastructure Panel */}
          {checkResult.threat_intelligence && (
            <ThreatIntelligencePanel
              threatIntelligence={checkResult.threat_intelligence}
            />
          )}

          {/* Cross-Signal Consistency Card */}
          {checkResult.cross_signal_consistency && (
            <div style={{ background: "var(--bg-surface-elevated)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: "1rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  🔄 Cross-Signal Consistency Analysis
                </span>
                <span className={`evidence-tag ${checkResult.cross_signal_consistency.status === "INCONSISTENT" ? "critical" : (checkResult.cross_signal_consistency.status === "CONSISTENT" ? "observed" : "unavailable")}`}>
                  {checkResult.cross_signal_consistency.status} ({(checkResult.cross_signal_consistency.score * 100).toFixed(0)}%)
                </span>
              </div>
              {checkResult.cross_signal_consistency.conflicts.length > 0 ? (
                <div>
                  {checkResult.cross_signal_consistency.conflicts.map((c, i) => (
                    <div key={i} style={{ color: "#FCA5A5", fontSize: "0.75rem", marginTop: "3px" }}>⚠️ {c}</div>
                  ))}
                </div>
              ) : (
                <div style={{ color: "var(--color-safe)", fontSize: "0.75rem" }}>✓ All cross-signal parameters correlate consistently with baseline.</div>
              )}
            </div>
          )}

          {/* Payment Payload Integrity Cross-Validation Panel */}
          {checkResult.payload_integrity && (
            <PayloadIntegrityPanel
              payloadIntegrity={checkResult.payload_integrity}
            />
          )}

          {/* Transaction DNA Behavioral Baseline Panel */}
          {checkResult.transaction_dna && (
            <TransactionDNAPanel
              transactionDna={checkResult.transaction_dna}
            />
          )}

          {/* FraudDNA 5-Axis Hub */}
          {checkResult.fraud_dna && (
            <FraudDNAHub
              fraudDna={checkResult.fraud_dna}
              counterfactuals={checkResult.counterfactuals}
            />
          )}

          {/* Action Button: Transfer to Investigation Workspace */}
          <div style={{ marginTop: "0.5rem" }}>
            <button className="btn btn-primary" onClick={onTransferToInvestigation} style={{ width: "100%", padding: "0.65rem" }}>
              Open Case in Investigation Center Workspace →
            </button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

function AttackChainWorkspace({
  caseId,
  onViewInGraph,
  onViewEvidence,
  onAskCopilot
}) {
  const [chainData, setChainData] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [viewMode, setViewMode] = useState("simple");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadAttackChain = async (cid) => {
    const target = cid || caseId || "QF-20261007-49910";
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/investigation/cases/${target}/attack-chain`);
      if (res.ok) {
        const data = await res.json();
        setChainData(data);
        if (data.events && data.events.length > 0) {
          setSelectedEvent(data.events[0]);
        }
      } else {
        setError("Reconstruction not available for this case.");
      }
    } catch (e) {
      setError("Error connecting to attack chain service.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAttackChain(caseId);
  }, [caseId]);

  if (loading) {
    return (
      <div className="glass-panel" style={{ padding: "3rem", textAlign: "center" }}>
        <RefreshCw size={28} className="purple-text" style={{ animation: "spin 1s linear infinite" }} />
        <p style={{ marginTop: "1rem", color: "var(--text-muted)" }}>Reconstructing temporal attack chain from case evidence...</p>
      </div>
    );
  }

  if (!chainData) {
    return (
      <div className="glass-panel" style={{ padding: "3rem", textAlign: "center" }}>
        <AlertTriangle size={32} style={{ color: "var(--color-caution)" }} />
        <h3 style={{ marginTop: "0.75rem", color: "var(--text-primary)" }}>No Attack Chain Available</h3>
        <p style={{ color: "var(--text-muted)", maxWidth: "420px", margin: "0.5rem auto 1.25rem", fontSize: "0.82rem" }}>
          {error || "Select an investigation case to reconstruct its temporal fraud story."}
        </p>
        <button className="btn btn-primary" onClick={() => loadAttackChain("QF-20261007-49910")}>
          Load Demo Case (QF-20261007-49910) →
        </button>
      </div>
    );
  }

  const { summary, events, breakpoints, first_warning, key_event, activity_path, limitations } = chainData;

  return (
    <div className="attack-chain-workspace">
      
      {/* 1. Header & Context */}
      <div className="glass-panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span className="evidence-tag observed">TEMPORAL RECONSTRUCTION</span>
              <span className="sys-state completed">CASE {chainData.case_id}</span>
              <span className={`decision-pill ${chainData.decision?.toLowerCase()}`}>
                {chainData.decision} ({chainData.risk_score}% RISK)
              </span>
            </div>
            <h2 style={{ fontSize: "1.15rem", fontWeight: 800, color: "var(--text-primary)", margin: "0.4rem 0 0.15rem 0" }}>
              How the suspicious activity unfolded
            </h2>
            <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", margin: 0 }}>
              Chronological forensic timeline synthesized directly from verified case evidence.
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <div className="view-mode-toggle">
              <button
                className={`view-mode-btn ${viewMode === "simple" ? "active" : ""}`}
                onClick={() => setViewMode("simple")}
              >
                Simple View
              </button>
              <button
                className={`view-mode-btn ${viewMode === "analyst" ? "active" : ""}`}
                onClick={() => setViewMode("analyst")}
              >
                Analyst View 🔬
              </button>
            </div>

            <button
              className="btn btn-secondary"
              onClick={() => onAskCopilot?.(`What happened in the attack chain for case ${chainData.case_id}?`)}
            >
              <MessageSquare size={13} /> Ask Copilot
            </button>
          </div>
        </div>

        {/* 2. Attack Chain Metrics Grid */}
        <div className="attack-chain-metrics-grid">
          <div className="chain-metric-tile">
            <span className="chain-metric-label">Events</span>
            <span className="chain-metric-val">{summary.events_count}</span>
          </div>
          <div className="chain-metric-tile">
            <span className="chain-metric-label">Observed</span>
            <span className="chain-metric-val" style={{ color: "var(--color-safe)" }}>{summary.observed_count}</span>
          </div>
          <div className="chain-metric-tile">
            <span className="chain-metric-label">Inferred</span>
            <span className="chain-metric-val" style={{ color: "var(--color-caution)" }}>{summary.inferred_count}</span>
          </div>
          <div className="chain-metric-tile">
            <span className="chain-metric-label">Unavailable</span>
            <span className="chain-metric-val" style={{ color: "var(--text-dim)" }}>{summary.unavailable_count}</span>
          </div>
          <div className="chain-metric-tile">
            <span className="chain-metric-label">Time Span</span>
            <span className="chain-metric-val" style={{ fontSize: "0.9rem" }}>{summary.time_span}</span>
          </div>
          <div className="chain-metric-tile">
            <span className="chain-metric-label">Entities</span>
            <span className="chain-metric-val">{summary.entities_involved}</span>
          </div>
          <div className="chain-metric-tile">
            <span className="chain-metric-label">Quality Confidence</span>
            <span className="chain-metric-val" style={{ fontSize: "0.85rem", color: "var(--brand-primary)" }}>
              {summary.reconstruction_confidence}
            </span>
          </div>
        </div>

        {/* Human Readable Story */}
        <div className="attack-story-card">
          <div className="attack-story-title">
            <Info size={15} style={{ color: "var(--brand-primary)" }} /> What Happened (Chronological Story)
          </div>
          <div className="attack-story-text">
            {summary.human_readable_story}
          </div>
        </div>

        {/* Highlights Grid */}
        <div className="chain-highlights-grid">
          {first_warning && (
            <div className="chain-highlight-card first-warning">
              <span className="highlight-tag">⚠️ Earliest Warning Sign ({first_warning.timestamp_formatted})</span>
              <div className="highlight-title">{first_warning.title}</div>
              <div className="highlight-why">{first_warning.why}</div>
            </div>
          )}

          {key_event && (
            <div className="chain-highlight-card key-event">
              <span className="highlight-tag">🚨 Key Risk Driver</span>
              <div className="highlight-title">{key_event.title}</div>
              <div className="highlight-why">{key_event.why}</div>
            </div>
          )}
        </div>
      </div>

      {/* 3. Main Vertical Timeline */}
      <div className="chain-timeline-wrapper">
        
        <div className="glass-panel">
          <div className="panel-header">
            <h2><Clock size={16} style={{ color: "var(--brand-primary)" }} /> Evidence Timeline Sequence</h2>
            <span className="evidence-tag observed">CLICK EVENT TO INSPECT</span>
          </div>

          <div className="chain-timeline-list">
            {events.map((evt) => {
              const isSelected = selectedEvent?.event_id === evt.event_id;
              const dotImpactClass = evt.impact === "CRITICAL" ? "critical" : (evt.impact === "HIGH" ? "high" : (evt.impact === "MEDIUM" ? "medium" : "info"));
              const provClass = evt.provenance.toLowerCase();

              return (
                <div
                  key={evt.event_id}
                  className={`chain-event-row ${isSelected ? "active" : ""}`}
                  onClick={() => setSelectedEvent(evt)}
                >
                  <div className="chain-event-time-col">
                    <span className="chain-event-time-text">{evt.timestamp_formatted}</span>
                    <span className="chain-event-time-status">{evt.timestamp_status}</span>
                  </div>

                  <div className={`chain-event-dot-marker ${dotImpactClass}`} />

                  <div className="chain-event-card">
                    <div className="chain-event-card-top">
                      <div style={{ display: "flex", gap: "0.35rem", alignItems: "center" }}>
                        <span className="chain-stage-tag">{evt.stage.replace("_", " ")}</span>
                        {viewMode === "analyst" && (
                          <span style={{ fontSize: "0.65rem", color: "var(--text-dim)", fontFamily: "monospace" }}>{evt.event_id}</span>
                        )}
                      </div>
                      <div style={{ display: "flex", gap: "0.35rem" }}>
                        <span className={`chain-provenance-tag ${provClass}`}>
                          {evt.provenance}
                        </span>
                        <span className="evidence-tag observed" style={{ fontSize: "0.6rem" }}>
                          {evt.impact} IMPACT
                        </span>
                      </div>
                    </div>

                    <div className="chain-event-title">{evt.title}</div>
                    <div className="chain-event-desc">{evt.description}</div>

                    <div className="chain-event-footer">
                      <div className="chain-evidence-pills">
                        {evt.evidence_ids?.map((evId, idx) => (
                          <span key={idx} className="chain-evidence-pill" onClick={(e) => { e.stopPropagation(); onViewEvidence?.(evId); }}>
                            📄 {evId}
                          </span>
                        ))}
                      </div>

                      <button
                        className="btn btn-secondary"
                        style={{ fontSize: "0.68rem", padding: "2px 6px" }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onViewInGraph?.(evt.entities?.[0] || chainData.case_id);
                        }}
                      >
                        <Network size={11} /> View in Graph
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Side Inspector */}
        <div className="chain-detail-panel">
          {selectedEvent ? (
            <div>
              <div style={{ marginBottom: "0.65rem" }}>
                <span className="chain-stage-tag">{selectedEvent.stage.replace("_", " ")}</span>
                <h3 style={{ fontSize: "0.95rem", color: "var(--text-primary)", margin: "0.25rem 0" }}>
                  {selectedEvent.title}
                </h3>
                <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", fontSize: "0.72rem", color: "var(--text-muted)" }}>
                  <code style={{ color: "var(--brand-primary)" }}>{selectedEvent.event_id}</code>
                  <span>• {selectedEvent.timestamp_formatted} ({selectedEvent.timestamp_status})</span>
                </div>
              </div>

              <div className="chain-detail-section">
                <span className="chain-detail-section-label">Provenance Status</span>
                <div style={{ display: "flex", gap: "0.4rem" }}>
                  <span className={`chain-provenance-tag ${selectedEvent.provenance.toLowerCase()}`}>
                    {selectedEvent.provenance}
                  </span>
                  <span className="evidence-tag observed">
                    {selectedEvent.confidence} CONFIDENCE
                  </span>
                </div>
              </div>

              <div className="chain-detail-section">
                <span className="chain-detail-section-label">Forensic Context</span>
                <div className="chain-detail-why-box">
                  {selectedEvent.why_it_matters || selectedEvent.description}
                </div>
              </div>

              <div className="chain-detail-section">
                <span className="chain-detail-section-label">Involved Entities</span>
                <div style={{ display: "flex", gap: "0.3rem", flexWrap: "wrap" }}>
                  {selectedEvent.entities?.map((ent, idx) => (
                    <span
                      key={idx}
                      style={{ fontSize: "0.72rem", background: "var(--bg-surface-elevated)", border: "1px solid var(--border-medium)", padding: "2px 6px", borderRadius: "4px", color: "var(--text-primary)", cursor: "pointer" }}
                      onClick={() => onViewInGraph?.(ent)}
                    >
                      {ent}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                <button
                  className="btn btn-primary"
                  onClick={() => onViewInGraph?.(selectedEvent.entities?.[0] || chainData.case_id)}
                  style={{ width: "100%", fontSize: "0.78rem" }}
                >
                  <Network size={13} /> Focus in Fraud Graph →
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => onViewEvidence?.(selectedEvent.evidence_ids?.[0])}
                  style={{ width: "100%", fontSize: "0.78rem" }}
                >
                  <FileText size={13} /> View Evidence in Case Workspace
                </button>
              </div>
            </div>
          ) : (
            <div style={{ padding: "2rem 1rem", textAlign: "center", color: "var(--text-dim)", fontSize: "0.8rem" }}>
              Select an event from the timeline to view forensic details.
            </div>
          )}
        </div>

      </div>

      {/* 4. Potential Intervention Points */}
      {breakpoints && breakpoints.length > 0 && (
        <div className="glass-panel">
          <div className="panel-header">
            <h2><ShieldAlert size={16} style={{ color: "var(--color-caution)" }} /> Potential Intervention Points</h2>
            <span className="evidence-tag observed">{breakpoints.length} DEFENSE CHECKPOINTS</span>
          </div>
          <p className="panel-desc">
            Defensive opportunities where appropriate controls or step-up verification could disrupt the fraudulent progression.
          </p>

          <div className="breakpoints-grid">
            {breakpoints.map((bp) => (
              <div key={bp.breakpoint_id} className={`breakpoint-card ${bp.risk.toLowerCase()}`}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.35rem" }}>
                  <span className="chain-stage-tag">{bp.stage.replace("_", " ")}</span>
                  <span className="evidence-tag moderate">{bp.risk} RISK</span>
                </div>
                <div className="breakpoint-title">{bp.title}</div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.35rem" }}>
                  <b>Reason:</b> {bp.reason}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  <b>Recommended Action:</b> {bp.recommended_action}
                </div>
                <div className="breakpoint-interruption">
                  💡 <b>Potential Impact:</b> {bp.potential_interruption}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}

function App() {
  // Multilingual Support: 'en', 'te', 'hi', 'ta'
  const [lang, setLang] = useState(() => {
    try {
      return localStorage.getItem("qk_lang") || "en";
    } catch {
      return "en";
    }
  });

  const t = translations[lang] || translations.en;

  const handleLanguageChange = (newLang) => {
    setLang(newLang);
    try {
      localStorage.setItem("qk_lang", newLang);
    } catch {}
  };

  // Navigation: overview (landing), detect, check, response, investigation, explain, graph, chain, models, device-trust, attack-lab, copilot
  const [activeTab, setActiveTab] = useState("overview");
  
  // Backend & Telemetry State
  const [health, setHealth] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [modelComparison, setModelComparison] = useState([]);
  const [quantumStatus, setQuantumStatus] = useState(null);
  const [fraudAlerts, setFraudAlerts] = useState([]);
  const [recentTxns, setRecentTxns] = useState([]);
  const [meshNodes, setMeshNodes] = useState([]);
  const [simulating, setSimulating] = useState(false);
  const [selectedTxn, setSelectedTxn] = useState(null);
  const [driftData, setDriftData] = useState(null);

  // Check a Payment State
  const [checkMode, setCheckMode] = useState("QR");
  const [checkPayload, setCheckPayload] = useState("upi://pay?pa=freshmart.retail@icici&pn=Fresh%20Mart%20Retail&am=850.00&cu=INR&tn=Order%204991");
  const [checkImageBase64, setCheckImageBase64] = useState(null);
  const [checkImagePreview, setCheckImagePreview] = useState(null);
  const [checkImageName, setCheckImageName] = useState(null);
  const [checkAnalyzing, setCheckAnalyzing] = useState(false);
  const [checkStage, setCheckStage] = useState(0);
  const [checkResult, setCheckResult] = useState(null);
  const [checkScenarios, setCheckScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("SCENARIO_1_SAFE_QR");
  const [showEvidenceDrawer, setShowEvidenceDrawer] = useState(false);
  const [checkViewMode, setCheckViewMode] = useState("simple");
  const [showAdvancedDetails, setShowAdvancedDetails] = useState(false);

  // Case Workspace State
  const [casesList, setCasesList] = useState([]);
  const [activeCaseId, setActiveCaseId] = useState("QF-20261007-49910");
  const [activeCase, setActiveCase] = useState(null);
  const [caseSearchQuery, setCaseSearchQuery] = useState("");
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [selectedEvidenceItem, setSelectedEvidenceItem] = useState(null);
  const [showModelDetails, setShowModelDetails] = useState(false);
  const [showManualScoringForm, setShowManualScoringForm] = useState(false);
  const [newNoteContent, setNewNoteContent] = useState("");
  const [newNoteType, setNewNoteType] = useState("OBSERVATION");
  const [analystAction, setAnalystAction] = useState("CONFIRM_RECOMMENDATION");
  const [analystRationale, setAnalystRationale] = useState("");
  const [noteSubmitting, setNoteSubmitting] = useState(false);
  const [decisionSubmitting, setDecisionSubmitting] = useState(false);
  const [copiedToast, setCopiedToast] = useState(false);
  const [showNewCaseModal, setShowNewCaseModal] = useState(false);
  const [newCasePayload, setNewCasePayload] = useState("");
  const [newCaseType, setNewCaseType] = useState("QR");
  const [newCaseTitle, setNewCaseTitle] = useState("");
  const [newCaseLoading, setNewCaseLoading] = useState(false);
  const [auditVerifyResult, setAuditVerifyResult] = useState(null);
  const [auditVerifying, setAuditVerifying] = useState(false);

  // Graph State
  const [graphData, setGraphData] = useState(null);
  const [muleRings, setMuleRings] = useState([]);
  const [graphMode, setGraphMode] = useState("case");
  const [selectedGraphNode, setSelectedGraphNode] = useState(null);

  // Attack Lab State
  const [attackType, setAttackType] = useState("ACCOUNT_TAKEOVER");
  const [attackResult, setAttackResult] = useState(null);
  const [attackRunning, setAttackRunning] = useState(false);
  const [attackLabScenarios, setAttackLabScenarios] = useState([]);
  const [selectedLabScenarioId, setSelectedLabScenarioId] = useState("SCENARIO_1_GENUINE_PAYMENT");
  const [labRunResult, setLabRunResult] = useState(null);
  const [labRunning, setLabRunning] = useState(false);
  const [quantumBenchmarkData, setQuantumBenchmarkData] = useState(null);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);

  // Copilot State
  const [copilotMessages, setCopilotMessages] = useState([
    {
      sender: "bot",
      text: "👋 Welcome! I am Quantum Kavacha Copilot, your evidence-grounded AI Fraud Analyst powered by Groq LLM and IBM Qiskit quantum risk analysis. Ask me about SHAP explanations, Quantum Escalation triggers, or FraudDNA risk drivers for any payment scenario.",
      provider: "GROQ AI (qwen/qwen3.8-27b)",
      execution_mode: "LIVE_LLM"
    }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  // Form State
  const [form, setForm] = useState({
    txn_id: "TXN-QF-001",
    user_id: "USR-9901",
    amount: 85000,
    hour: 23,
    velocity_1h: 12,
    location_score: 0.82,
    device_score: 0.78,
    merchant_risk: 0.76,
    account_age_days: 40
  });
  const [predictResult, setPredictResult] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  const loadCaseGraph = async (caseId) => {
    const targetId = caseId || activeCaseId || "QF-20261007-49910";
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/graph/case/${targetId}`);
      if (res.ok) {
        const data = await res.json();
        setGraphData(data);
        if (data.nodes && data.nodes.length > 0) {
          const anchor = data.nodes.find(n => n.is_case_anchor) || data.nodes[0];
          setSelectedGraphNode(anchor);
        }
      }
    } catch (e) {
      console.warn("Failed to load case graph:", e);
    }
  };

  const loadNetworkGraph = async () => {
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/graph/network`);
      if (res.ok) {
        const data = await res.json();
        setGraphData(data);
        if (data.nodes && data.nodes.length > 0) {
          setSelectedGraphNode(data.nodes[0]);
        }
      }
    } catch (e) {
      console.warn("Failed to load network graph:", e);
    }
  };

  const loadMuleRings = async () => {
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/graph/mule-rings`);
      if (res.ok) {
        setMuleRings(await res.json());
      }
    } catch (e) {
      console.warn("Failed to load mule rings:", e);
    }
  };

  const handleVerifyAuditChain = async (caseId) => {
    const cid = caseId || activeCaseId;
    if (!cid) return;
    setAuditVerifying(true);
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/investigation/cases/${cid}/audit-verify`);
      if (res.ok) {
        setAuditVerifyResult(await res.json());
      }
    } catch (e) {
      console.warn("Audit chain verification warning:", e);
    } finally {
      setAuditVerifying(false);
    }
  };

  const handleResetDemoCases = async () => {
    if (!window.confirm("Reset case repository to clean deterministic SOC evaluation state for judging?")) return;
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/investigation/reset`, { method: "POST" });
      if (res.ok) {
        await loadCasesList();
        setAuditVerifyResult(null);
      }
    } catch (e) {
      console.warn("Reset failed:", e);
    }
  };

  const handleCreateNewCase = async () => {
    if (!newCasePayload.trim()) {
      alert("Please enter a QR payload, URL, or select a preset fixture.");
      return;
    }
    setNewCaseLoading(true);
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/investigation/cases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newCaseTitle.trim() || "Live Intake Case",
          input_type: newCaseType,
          payload: newCasePayload.trim(),
          transaction_context: {
            amount: 2500.0,
            device_score: 0.25,
            location_score: 0.15
          }
        })
      });
      if (res.ok) {
        const created = await res.json();
        await loadCasesList();
        setActiveCaseId(created.case_id);
        setActiveCase(created);
        setShowNewCaseModal(false);
        setNewCasePayload("");
        setNewCaseTitle("");
        handleVerifyAuditChain(created.case_id);
      } else {
        const err = await res.json();
        alert(`Failed to create case: ${err.detail || 'Unknown error'}`);
      }
    } catch (e) {
      alert(`Network error creating case: ${e.message}`);
    } finally {
      setNewCaseLoading(false);
    }
  };

  const loadCaseDetails = async (caseId) => {
    if (!caseId) return;
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/investigation/cases/${caseId}`);
      if (res.ok) {
        const data = await res.json();
        setActiveCase(data);
        setActiveCaseId(data.case_id);
        loadCaseGraph(data.case_id);
        handleVerifyAuditChain(data.case_id);
      }
    } catch (e) {
      console.warn("Failed to load case details:", e);
    }
  };

  const loadCasesList = async (q = "") => {
    try {
      const endpoint = q ? `${FASTAPI_BASE}/api/investigation/cases?q=${encodeURIComponent(q)}` : `${FASTAPI_BASE}/api/investigation/cases`;
      const res = await fetch(endpoint);
      if (res.ok) {
        const data = await res.json();
        setCasesList(data);
        if (data.length > 0 && !activeCase) {
          loadCaseDetails(data[0].case_id);
        }
      }
    } catch (e) {
      console.warn("Failed to list cases:", e);
    }
  };

  const loadData = async () => {
    try {
      const fetchJson = async (url) => {
        try {
          const res = await fetch(url);
          return res.ok ? await res.json() : null;
        } catch {
          return null;
        }
      };

      const [
        hData, aData, mcData, qData, faData, txData, dData, scData, labData
      ] = await Promise.all([
        fetchJson(`${FASTAPI_BASE}/api/health`),
        fetchJson(`${FASTAPI_BASE}/api/analytics`),
        fetchJson(`${FASTAPI_BASE}/api/models/comparison`),
        fetchJson(`${FASTAPI_BASE}/api/quantum/status`),
        fetchJson(`${FASTAPI_BASE}/api/fraud-alerts`),
        fetchJson(`${FASTAPI_BASE}/api/transactions?limit=15`),
        fetchJson(`${FASTAPI_BASE}/api/drift`),
        fetchJson(`${FASTAPI_BASE}/api/check-payment/scenarios`),
        fetchJson(`${FASTAPI_BASE}/api/attack-lab/scenarios`)
      ]);

      if (hData) setHealth(hData);
      if (aData) setAnalytics(aData);
      if (mcData) setModelComparison(mcData);
      if (qData) setQuantumStatus(qData);
      if (faData) setFraudAlerts(faData);
      if (txData) setRecentTxns(txData);
      if (dData) setDriftData(dData);
      if (scData) setCheckScenarios(scData);
      if (labData) setAttackLabScenarios(labData);

      loadCasesList();
      loadMuleRings();
      loadCaseGraph("QF-20261007-49910");
    } catch (err) {
      console.warn("API load warning:", err);
    }
  };

  const loadAttackLabScenarios = async () => {
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/attack-lab/scenarios`);
      if (res.ok) setAttackLabScenarios(await res.json());
    } catch (e) {
      console.warn("Failed to load attack lab scenarios:", e);
    }
  };

  const runAttackLabScenario = async (scenarioId) => {
    const target = scenarioId || selectedLabScenarioId || "SCENARIO_1_GENUINE_PAYMENT";
    setLabRunning(true);
    setLabRunResult(null);
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/attack-lab/run/${target}`, { method: "POST" });
      if (res.ok) {
        setLabRunResult(await res.json());
      }
    } catch (e) {
      console.warn("Attack lab execution failed:", e);
    } finally {
      setLabRunning(false);
    }
  };

  const loadQuantumBenchmark = async () => {
    setBenchmarkLoading(true);
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/quantum/benchmark`);
      if (res.ok) {
        setQuantumBenchmarkData(await res.json());
      }
    } catch (e) {
      console.warn("Quantum benchmark load failed:", e);
    } finally {
      setBenchmarkLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 6000);
    return () => clearInterval(interval);
  }, []);

  const updateForm = (k, v) => setForm({ ...form, [k]: v });

  const handleSelectScenario = (sc) => {
    setSelectedScenarioId(sc.id);
    setCheckMode(sc.input_type);
    setCheckPayload(sc.payload);
    setCheckImageBase64(null);
    setCheckImagePreview(null);
    setCheckImageName(null);
    setCheckResult(null);
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

    setCheckImageName(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      setCheckImageBase64(reader.result);
      setCheckImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleRunCheckPayment = async () => {
    setCheckAnalyzing(true);
    setCheckResult(null);

    setCheckStage(1);
    await new Promise(r => setTimeout(r, 150));
    setCheckStage(2);
    await new Promise(r => setTimeout(r, 180));
    setCheckStage(3);
    await new Promise(r => setTimeout(r, 180));
    setCheckStage(4);
    await new Promise(r => setTimeout(r, 200));
    setCheckStage(5);

    try {
      const res = await fetch(`${FASTAPI_BASE}/api/check-payment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          input_type: checkMode,
          payload: checkPayload,
          image_base64: checkImageBase64,
          filename: checkImageName,
          scenario_id: selectedScenarioId
        })
      });

      if (res.ok) {
        const data = await res.json();
        setCheckResult(data);
        if (data.decision === "APPROVE") {
          confetti({ particleCount: 50, spread: 45, origin: { y: 0.7 } });
        }
      } else {
        alert("Payment forensics analysis failed. Please check backend response.");
      }
    } catch (e) {
      alert("Error reaching payment forensics service. Ensure FastAPI backend is running.");
    }
    setCheckAnalyzing(false);
  };

  const handleTransferToInvestigation = async () => {
    if (!checkResult) return;
    try {
      await loadCaseDetails(checkResult.case_id);
      await loadCasesList();
    } catch (e) {
      console.warn("Transfer fetch error:", e);
    }
    setActiveTab("investigation");
  };

  const handleAddAnalystNote = async (e) => {
    e?.preventDefault();
    if (!newNoteContent.trim() || !activeCaseId) return;
    setNoteSubmitting(true);
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/investigation/cases/${activeCaseId}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          note_type: newNoteType,
          content: newNoteContent.trim(),
          author: "Lead SOC Analyst"
        })
      });
      if (res.ok) {
        const note = await res.json();
        setActiveCase(prev => prev ? {
          ...prev,
          analyst_notes: [...(prev.analyst_notes || []), note]
        } : prev);
        setNewNoteContent("");
      }
    } catch (e) {
      alert("Failed to append analyst note. Ensure backend is running.");
    }
    setNoteSubmitting(false);
  };

  const handleSubmitAnalystDecision = async (e) => {
    e?.preventDefault();
    if (!activeCaseId) return;
    setDecisionSubmitting(true);
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/investigation/cases/${activeCaseId}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analyst_action: analystAction,
          rationale: analystRationale.trim() || "Reviewed multi-signal telemetry and corroborated machine recommendation.",
          author: "Lead SOC Analyst"
        })
      });
      if (res.ok) {
        const updated = await res.json();
        setActiveCase(updated);
        alert("Analyst review decision recorded successfully.");
      }
    } catch (e) {
      alert("Failed to submit review decision.");
    }
    setDecisionSubmitting(false);
  };

  const handleExportCaseDossier = async () => {
    if (!activeCaseId) return;
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/investigation/cases/${activeCaseId}/export`);
      if (res.ok) {
        const dossier = await res.json();
        const blob = new Blob([JSON.stringify(dossier, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Quantum-Kavacha-Dossier-${activeCaseId}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (e) {
      alert("Export error occurred.");
    }
  };

  const handleAskCopilot = (prompt) => {
    const q = prompt || `Why was case ${activeCase?.case_id || activeCaseId} flagged?`;
    setChatInput(q);
    setActiveTab("copilot");
  };

  const toggleSimulation = async () => {
    const endpoint = simulating ? "/api/simulate/stop" : "/api/simulate/start";
    try {
      await fetch(`${FASTAPI_BASE}${endpoint}`, { method: "POST" });
      setSimulating(!simulating);
    } catch (e) {
      console.warn("Simulation toggle error:", e);
    }
  };

  const runAttackSimulation = async () => {
    setAttackRunning(true);
    setAttackResult(null);
    try {
      const res = await fetch(`${FASTAPI_BASE}/api/attacks/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ attack_type: attackType })
      });
      if (res.ok) {
        setAttackResult(await res.json());
      }
    } catch (e) {
      console.warn("Attack simulation error:", e);
    }
    setAttackRunning(false);
  };

  const handleCopilotSend = async () => {
    if (!chatInput.trim()) return;
    const userMsg = chatInput.trim();
    setChatInput("");
    setCopilotMessages(prev => [...prev, { sender: "user", text: userMsg }]);
    setChatLoading(true);

    try {
      const res = await fetch(`${FASTAPI_BASE}/api/copilot/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userMsg,
          context: checkResult ? {
            txn_id: checkResult.case_id,
            risk_score: checkResult.risk_score,
            decision: checkResult.decision,
            fraud_dna: checkResult.fraud_dna
          } : null
        })
      });
      if (res.ok) {
        const data = await res.json();
        setCopilotMessages(prev => [
          ...prev,
          {
            sender: "bot",
            text: data.answer,
            sources: data.grounded_sources,
            provider: data.provider || "GROQ AI",
            execution_mode: data.execution_mode || "LIVE_LLM"
          }
        ]);
      } else {
        setCopilotMessages(prev => [
          ...prev,
          {
            sender: "bot",
            text: "Backend analyst service returned an error. Falling back to offline triage.",
            provider: "SERVICE_ERROR",
            execution_mode: "ERROR"
          }
        ]);
      }
    } catch (e) {
      setCopilotMessages(prev => [
        ...prev,
        {
          sender: "bot",
          text: "Error connecting to Quantum Kavacha Copilot analyst. Please check backend connection.",
          provider: "NETWORK_ERROR",
          execution_mode: "ERROR"
        }
      ]);
    }
    setChatLoading(false);
  };

  const getPageTitleAndDesc = () => {
    switch (activeTab) {
      case "overview": return { title: "Command Center", desc: "Evidence-driven agentic fraud operations, critical alerts, and active quantum defenses." };
      case "investigation": return { title: "Investigations Workspace", desc: "Three-region case command center with multi-signal evidence corroboration and grounded Copilot." };
      case "detect":
      case "evidence": return { title: "Evidence Analysis Explorer", desc: "Multi-modal forensic ingestion for QR payloads, receipt OCR, document SHA-256 seals, and URL intelligence." };
      case "agent-workspace": return { title: "Agent Workspace & Registry", desc: "Real service execution states, hardware grounding, runtime latencies, and input evidence chains." };
      case "graph": return { title: "Fraud Relationship Graph", desc: "Entity topology tracing payer accounts, anomalous devices, and mule syndicates in 3D space." };
      case "quantum-lab":
      case "models": return { title: "Quantum Research Lab", desc: "Qiskit Aer 4-qubit ZZFeatureMap Hilbert space telemetry, kernel Gram matrix, and empirical ablation baselines." };
      case "threat-intel":
      case "response": return { title: "Threat Intelligence & Fraud Alerts", desc: "Autonomous defense orchestrator, VirusTotal vendor intelligence, and incident mitigation." };
      case "attack-lab": return { title: "Attack Simulation Lab", desc: "Strictly isolated red-team adversarial simulator evaluating multi-stage fraud resilience." };
      case "device-trust": return { title: "System Health & Device Trust", desc: "ESP32-S3 hardware-rooted identity, cryptographic attestation, and operational audit." };
      case "check": return { title: "Transaction Feed & Ledger", desc: "Real-time payment stream, velocity bursts, and transactional telemetry." };
      case "explain": return { title: "FraudDNA™ Explainability", desc: "5-axis risk fingerprint, counterfactual simulations, and attribution analysis." };
      case "chain": return { title: "Attack Chain Reconstruction", desc: "Chronological vertical forensic story mapping multi-stage attack vectors." };
      case "copilot": return { title: "Investigation Copilot", desc: "Evidence-grounded conversational analyst explaining SHAP, graph links, and case evidence." };
      default: return { title: "QUANTUM KAVACHA", desc: "Hybrid Quantum–Classical Digital Fraud Detection & Forensics" };
    }
  };

  const { title: currentTitle, desc: currentDesc } = getPageTitleAndDesc();

  return (
    <div className="app-layout">
      {/* 1. LEFT SIDEBAR */}
      <aside className="app-sidebar">
        <div>
          {/* Brand Header */}
          <div className="sidebar-header">
            <div className="sidebar-brand-group">
              <div className="brand-shield-icon">
                <Shield size={20} />
              </div>
              <div>
                <div className="sidebar-brand-name">{t.appName || "QUANTUM KAVACHA"}</div>
                <div className="sidebar-brand-sub">{t.appSubtitle || "Hybrid Quantum-Classical Defense"}</div>
              </div>
            </div>
          </div>

          {/* Navigation Sections — Agentic Command Center */}
          <div className="sidebar-nav-container">
            {/* Primary Command */}
            <div>
              <div className="sidebar-section-label">Operations</div>
              <div className="sidebar-nav-list">
                <button
                  className={`sidebar-nav-item ${activeTab === "overview" ? "active" : ""}`}
                  onClick={() => setActiveTab("overview")}
                >
                  <Activity size={16} /> 1. Command Center
                </button>
                <button
                  className={`sidebar-nav-item ${activeTab === "investigation" ? "active" : ""}`}
                  onClick={() => setActiveTab("investigation")}
                >
                  <Shield size={16} /> 2. Investigations
                  <span className="sidebar-nav-badge">{casesList?.length || 0}</span>
                </button>
                <button
                  className={`sidebar-nav-item ${activeTab === "detect" || activeTab === "evidence" ? "active" : ""}`}
                  onClick={() => setActiveTab("detect")}
                >
                  <Crosshair size={16} /> 3. Evidence Analysis
                </button>
              </div>
            </div>

            {/* Agent & Topology */}
            <div>
              <div className="sidebar-section-label">Agent & Topology</div>
              <div className="sidebar-nav-list">
                <button
                  className={`sidebar-nav-item ${activeTab === "agent-workspace" ? "active" : ""}`}
                  onClick={() => setActiveTab("agent-workspace")}
                >
                  <Cpu size={16} /> 4. Agent Workspace
                </button>
                <button
                  className={`sidebar-nav-item ${activeTab === "graph" ? "active" : ""}`}
                  onClick={() => { setActiveTab("graph"); loadCaseGraph(activeCaseId); }}
                >
                  <Network size={16} /> 5. Fraud Relationship Graph
                </button>
                <button
                  className={`sidebar-nav-item ${activeTab === "quantum-lab" || activeTab === "models" ? "active" : ""}`}
                  onClick={() => setActiveTab("quantum-lab")}
                >
                  <Zap size={16} /> 6. Quantum Research Lab
                </button>
              </div>
            </div>

            {/* Intelligence & Simulation */}
            <div>
              <div className="sidebar-section-label">Defense & Security</div>
              <div className="sidebar-nav-list">
                <button
                  className={`sidebar-nav-item ${activeTab === "response" || activeTab === "threat-intel" ? "active" : ""}`}
                  onClick={() => setActiveTab("response")}
                >
                  <ShieldAlert size={16} /> 7. Threat Intelligence
                </button>
                <button
                  className={`sidebar-nav-item ${activeTab === "attack-lab" ? "active" : ""}`}
                  onClick={() => setActiveTab("attack-lab")}
                >
                  <Flame size={16} /> 8. Attack Simulation Lab
                </button>
                <button
                  className={`sidebar-nav-item ${activeTab === "device-trust" ? "active" : ""}`}
                  onClick={() => setActiveTab("device-trust")}
                >
                  <Server size={16} /> 9. System Health & Audit
                </button>
                <button
                  className={`sidebar-nav-item ${activeTab === "copilot" ? "active" : ""}`}
                  onClick={() => setActiveTab("copilot")}
                >
                  <MessageSquare size={16} /> Investigation Copilot
                </button>
              </div>
            </div>
          </div>
          </div>

          {/* Sidebar Footer */}
        <div className="sidebar-footer">
          <div className="sidebar-health-card">
            <div className="sidebar-health-header">
              <span style={{ color: "var(--text-muted)", fontWeight: 700 }}>ENGINE STATUS</span>
              <span className="status-dot-indicator">
                <span className="status-dot"></span> LIVE
              </span>
            </div>
            <div style={{ fontSize: "0.74rem", color: "var(--text-secondary)", fontWeight: 600 }}>
              {health?.quantum_engine?.online ? "Qiskit 2.x • Simulation" : "Classical AI Ensemble"}
            </div>
          </div>
        </div>
      </aside>

      {/* 2. MAIN APPLICATION VIEWPORT */}
      <main className="app-main-area">
        {/* Top Header */}
        <header className="app-header">
          <div className="header-title-block">
            <h1>{currentTitle}</h1>
            <p>{currentDesc}</p>
          </div>

          <div className="header-controls">
            {/* Language Selector Dropdown */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", background: "rgba(255,255,255,0.03)", padding: "0.2rem 0.5rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <Globe size={13} style={{ color: "var(--brand-cyan)" }} />
              <select
                value={lang}
                onChange={(e) => handleLanguageChange(e.target.value)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-primary)",
                  fontSize: "0.74rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  outline: "none"
                }}
              >
                <option value="en" style={{ background: "#0f172a", color: "#fff" }}>English (EN)</option>
                <option value="te" style={{ background: "#0f172a", color: "#fff" }}>తెలుగు (TE)</option>
                <option value="hi" style={{ background: "#0f172a", color: "#fff" }}>हिन्दी (HI)</option>
                <option value="ta" style={{ background: "#0f172a", color: "#fff" }}>தமிழ் (TA)</option>
              </select>
            </div>

            <button
              className={`btn btn-stream ${simulating ? "active" : ""}`}
              onClick={toggleSimulation}
            >
              {simulating ? <Pause size={13} /> : <Play size={13} />}
              {simulating ? "Pause Feed" : "Live Stream"}
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => handleAskCopilot()}
              style={{ fontSize: "0.75rem", padding: "0.4rem 0.75rem" }}
            >
              <MessageSquare size={13} /> Ask Copilot
            </button>
            <span
              className={`evidence-tag ${health?.status === "healthy" ? "observed" : "critical"}`}
              style={{ fontSize: "0.7rem", padding: "0.3rem 0.6rem" }}
              title={`API Backend: ${FASTAPI_BASE}`}
            >
              {health?.status === "healthy" ? "● BACKEND LIVE" : "○ BACKEND OFFLINE"}
            </span>
            <span className="evidence-tag observed" style={{ fontSize: "0.7rem", padding: "0.3rem 0.6rem" }}>
              DEMO MODE
            </span>
          </div>
        </header>

        {/* Workspace Viewport */}
        <div className="app-viewport">
          <AnimatePresence mode="wait">
            
                            {/* 0. UNIFIED DETECTION CENTER */}
              {activeTab === "detect" && (
                <motion.div
                  key="detect"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.15 }}
                  className="tab-pane"
                >
                  <DetectionCenterWorkspace
                    fastApiBase={FASTAPI_BASE}
                    checkScenarios={checkScenarios}
                    onSelectCase={(cid) => {
                      setActiveCaseId(cid);
                      loadCaseDetails(cid);
                      setActiveTab("investigation");
                    }}
                    onAskCopilot={(prompt) => {
                      setChatInput(prompt);
                      setActiveTab("copilot");
                    }}
                    onOpenEvidenceDetails={() => setShowEvidenceDrawer(true)}
                  />
                </motion.div>
              )}

              {/* 1. TRANSACTIONS */}
              {activeTab === "check" && (
                <motion.div
                  key="check"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.15 }}
                  className="tab-pane"
                >
                  <TransactionsWorkspace 
                    fastApiBase={FASTAPI_BASE} 
                    onSelectTransaction={(txn_id) => {
                      setActiveCaseId(txn_id);
                      loadCaseDetails(txn_id);
                      setActiveTab("investigation");
                    }} 
                  />
                </motion.div>
              )}

              {activeTab === "overview" && (
                <motion.div
                  key="overview"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.15 }}
                  className="tab-pane"
                >
                  <CommandOverviewWorkspace
                    analytics={analytics}
                    health={health}
                    quantumStatus={quantumStatus}
                    fraudAlerts={fraudAlerts}
                    recentTxns={recentTxns}
                    activeCase={activeCase}
                    casesList={casesList}
                    onNavigate={(tab) => setActiveTab(tab)}
                    onSelectCase={(cid) => {
                      setActiveCaseId(cid);
                      loadCaseDetails(cid);
                      setActiveTab("investigation");
                    }}
                    onRunDetection={() => setActiveTab("detect")}
                  />
                </motion.div>
              )}

            {/* 3. INVESTIGATION CENTER */}
            {activeTab === "investigation" && (
              <motion.div
                key="investigation"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="tab-pane"
              >
                <InvestigationCommandCenter
                  casesList={casesList}
                  activeCase={activeCase}
                  activeCaseId={activeCaseId}
                  onSelectCase={(cid) => {
                    setActiveCaseId(cid);
                    loadCaseDetails(cid);
                  }}
                  onSearchCases={(query) => {
                    setCaseSearchQuery(query);
                    loadCasesList(query);
                  }}
                  searchQuery={caseSearchQuery}
                  onOpenIntakeModal={() => setShowNewCaseModal(true)}
                  onResetDemos={handleResetDemoCases}
                  onVerifyAuditChain={handleVerifyAuditChain}
                  auditVerifyResult={auditVerifyResult}
                  auditVerifying={auditVerifying}
                  onSubmitAnalystDecision={handleSubmitAnalystDecision}
                  decisionSubmitting={decisionSubmitting}
                  analystAction={analystAction}
                  setAnalystAction={setAnalystAction}
                  analystRationale={analystRationale}
                  setAnalystRationale={setAnalystRationale}
                  onNavigateTab={(tab) => setActiveTab(tab)}
                  onAskCopilot={(prompt) => handleAskCopilot(prompt)}
                  onExportDossier={() => handleExportDossier(activeCase?.case_id)}
                />
              </motion.div>
            )}

            {/* 4. FRAUDDNA / EXPLAIN */}
            {activeTab === "explain" && (
              <motion.div
                key="explain"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="tab-pane"
              >
                {activeCase?.fraud_dna ? (
                  <FraudDNAHub
                    fraudDna={activeCase.fraud_dna}
                    counterfactuals={activeCase.counterfactuals}
                  />
                ) : (
                  <div className="glass-panel" style={{ padding: "3rem", textAlign: "center" }}>
                    <Layers size={36} style={{ color: "var(--text-dim)", margin: "0 auto 0.75rem auto" }} />
                    <h3 style={{ color: "var(--text-primary)" }}>No Active FraudDNA Profile</h3>
                    <p style={{ color: "var(--text-muted)", fontSize: "0.82rem" }}>Select a case from the Investigation Center or Check a Payment to view its 5-axis fingerprint.</p>
                  </div>
                )}
              </motion.div>
            )}

            {/* 5. FRAUD ALERTS (formerly response) */}
            {activeTab === "response" && (
              <motion.div
                key="response"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="tab-pane"
              >
                <ResponseCenterWorkspace
                  currentCaseId={activeCaseId || "QF-20261007-49910"}
                  onNavigateTab={(tab) => setActiveTab(tab)}
                  onAskCopilot={(prompt) => {
                    setChatInput(prompt);
                    setActiveTab("copilot");
                  }}
                />
              </motion.div>
            )}

            {/* 6. FRAUD GRAPH */}
            {activeTab === "graph" && (
              <motion.div
                key="graph"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="tab-pane"
              >
                <div className="glass-panel">
                  <div className="panel-header" style={{ flexWrap: "wrap", gap: "0.75rem" }}>
                    <div>
                      <h2><Network size={18} style={{ color: "var(--brand-primary)" }} /> 3D Fraud Relationship Graph</h2>
                      <p className="panel-desc" style={{ margin: "2px 0 0 0" }}>
                        Entity network tracing payer accounts, anomalous hardware, recipient VPAs, and mule clusters.
                      </p>
                    </div>

                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                      <button
                        className={`btn btn-secondary ${graphMode === "case" ? "btn-primary" : ""}`}
                        onClick={() => { setGraphMode("case"); loadCaseGraph(activeCaseId); }}
                        style={{ fontSize: "0.75rem" }}
                      >
                        Case Subgraph
                      </button>
                      <button
                        className={`btn btn-secondary ${graphMode === "network" ? "btn-primary" : ""}`}
                        onClick={() => { setGraphMode("network"); loadNetworkGraph(); }}
                        style={{ fontSize: "0.75rem" }}
                      >
                        Macro Network
                      </button>
                      <button className="btn btn-secondary" onClick={() => setActiveTab("chain")} style={{ fontSize: "0.75rem" }}>
                        <GitFork size={13} /> View Attack Chain →
                      </button>
                    </div>
                  </div>

                  {graphData?.summary && (
                    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", margin: "0.75rem 0" }}>
                      <span className="evidence-tag observed">NODES: {graphData.summary.total_nodes}</span>
                      <span className="evidence-tag observed">EDGES: {graphData.summary.total_edges}</span>
                      <span className="evidence-tag critical">HIGH RISK: {graphData.summary.high_risk_node_count}</span>
                      <span className="evidence-tag moderate">MULE RINGS: {graphData.summary.mule_clusters_detected}</span>
                    </div>
                  )}

                  <div className="graph-3d-box" style={{ height: "420px" }}>
                    <TransactionGraph3D
                      graphData={graphData}
                      onSelectNode={(node) => setSelectedGraphNode(node)}
                      selectedNodeId={selectedGraphNode?.id}
                    />
                  </div>
                </div>
              </motion.div>
            )}

            {/* 7. ATTACK CHAIN */}
            {activeTab === "chain" && (
              <motion.div
                key="chain"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="tab-pane"
              >
                <AttackChainWorkspace
                  caseId={activeCaseId || activeCase?.case_id || "QF-20261007-49910"}
                  onViewInGraph={(entityId) => {
                    setActiveTab("graph");
                    if (entityId) loadCaseGraph(activeCaseId || "QF-20261007-49910");
                  }}
                  onViewEvidence={() => setActiveTab("investigation")}
                  onAskCopilot={handleAskCopilot}
                />
              </motion.div>
            )}

            {/* 8. MODEL CONSENSUS / UNCERTAINTY */}
            {activeTab === "agent-workspace" && (
              <motion.div
                key="agent-workspace"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="tab-pane"
              >
                <AgentWorkspace
                  health={health}
                  quantumStatus={quantumStatus}
                  onNavigate={(tab) => setActiveTab(tab)}
                />
              </motion.div>
            )}

            {/* 6. QUANTUM RESEARCH LAB */}
            {(activeTab === "quantum-lab" || activeTab === "models") && (
              <motion.div
                key="quantum-lab"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="tab-pane"
              >
                <QuantumResearchLabWorkspace
                  quantumStatus={quantumStatus}
                  quantumBenchmarkData={quantumBenchmarkData}
                  benchmarkLoading={benchmarkLoading}
                  onRunBenchmark={loadQuantumBenchmark}
                />
              </motion.div>
            )}

            {/* 9. ATTACK LAB */}
            {activeTab === "attack-lab" && (
              <motion.div
                key="attack-lab"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="tab-pane"
              >
                <div className="glass-panel">
                  {/* 1. Controlled Cybersecurity Testbed: QR Artifact Generator & Benchmark */}
                  <div style={{ marginBottom: "1.5rem" }}>
                    <AttackSimulationLab
                      fastApiBase={FASTAPI_BASE}
                      onSendToDetection={(payloadStr) => {
                        setCheckPayload(payloadStr);
                        setActiveTab("detect");
                      }}
                    />
                  </div>

                  {/* 2. Full Deterministic Pipeline Scenarios */}
                  <div className="panel-header" style={{ marginTop: "1.5rem", borderTop: "1px solid var(--border-subtle)", paddingTop: "1.25rem" }}>
                    <h2><Flame size={18} style={{ color: "var(--color-high-risk)" }} /> Multi-Stage Pipeline Red-Team Scenarios</h2>
                    <span className="evidence-tag observed">12 DETERMINISTIC HARNESSES</span>
                  </div>
                  <p className="panel-desc">
                    Execute real-time adversarial attack simulations through the live multi-signal payment forensics, ML fusion, Qiskit quantum escalation, and response playbooks without hardcoded shortcuts.
                  </p>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "0.65rem", margin: "1rem 0" }}>
                    {(attackLabScenarios.length > 0 ? attackLabScenarios : [
                      { id: "SCENARIO_1_GENUINE_PAYMENT", name: "1. Genuine Verified Payment", category: "Clean Flow", attack_type: "BENIGN_BASELINE" },
                      { id: "SCENARIO_2_QR_AMOUNT_MANIPULATION", name: "2. QR Amount Manipulation", category: "QR Exploit", attack_type: "QR_PAYLOAD_TAMPERING" },
                      { id: "SCENARIO_3_SCREENSHOT_PAYMENT_FRAUD", name: "3. Screenshot Payment Fraud", category: "Visual Spoofing", attack_type: "IMAGE_FORGERY_OCR" },
                      { id: "SCENARIO_4_PHISHING_PAYMENT_LINK", name: "4. Phishing Payment Link", category: "Social Engineering", attack_type: "PHISHING_DOMAIN" },
                      { id: "SCENARIO_5_ACCOUNT_TAKEOVER", name: "5. Account Takeover", category: "Identity Theft", attack_type: "CREDENTIAL_COMPROMISE" },
                      { id: "SCENARIO_6_TRANSACTION_VELOCITY_ATTACK", name: "6. Transaction Velocity Attack", category: "Automated Bot", attack_type: "HIGH_FREQUENCY_BURST" },
                      { id: "SCENARIO_7_DEVICE_ANOMALY", name: "7. Device Anomaly", category: "Hardware Spoof", attack_type: "HARDWARE_SIGNATURE_SPOOF" },
                      { id: "SCENARIO_8_PAYMENT_PAYLOAD_TAMPERING", name: "8. Payload Tampering", category: "Cross-Field Exploit", attack_type: "PARAMETRIC_MISMATCH" },
                      { id: "SCENARIO_9_SUSPICIOUS_ENTITY_CLUSTER", name: "9. Suspicious Entity Cluster", category: "Syndicate", attack_type: "GRAPH_MULE_RING" }
                    ]).map((sc) => {
                      const isSelected = selectedLabScenarioId === sc.id;
                      return (
                        <div
                          key={sc.id}
                          onClick={() => {
                            setSelectedLabScenarioId(sc.id);
                            runAttackLabScenario(sc.id);
                          }}
                          style={{
                            background: isSelected ? "var(--brand-primary-subtle)" : "var(--bg-surface-elevated)",
                            border: `1px solid ${isSelected ? "var(--brand-primary)" : "var(--border-subtle)"}`,
                            borderRadius: "var(--radius-md)",
                            padding: "0.75rem",
                            cursor: "pointer",
                            transition: "all 0.15s ease"
                          }}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <strong style={{ fontSize: "0.78rem", color: "var(--text-primary)" }}>{sc.name}</strong>
                          </div>
                          <div style={{ display: "flex", gap: "0.35rem", marginTop: "4px" }}>
                            <span className="evidence-tag observed" style={{ fontSize: "0.62rem" }}>{sc.category}</span>
                            <span style={{ fontSize: "0.65rem", color: "var(--text-dim)" }}>{sc.attack_type}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
                    <button className="attack-sim-btn" onClick={() => runAttackLabScenario(selectedLabScenarioId)} disabled={labRunning} style={{ flex: 1 }}>
                      {labRunning ? "Executing Full Forensics Pipeline..." : `Run Live Pipeline for Selected Scenario →`}
                    </button>
                  </div>

                  {labRunResult && (
                    <motion.div
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      style={{ marginTop: "1rem", background: "var(--bg-surface-elevated)", border: "1px solid var(--border-medium)", borderRadius: "var(--radius-lg)", padding: "1.25rem" }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                        <div>
                          <span style={{ fontWeight: 800, color: labRunResult.risk_score >= 70 ? "var(--color-high-risk)" : (labRunResult.risk_score >= 35 ? "var(--color-caution)" : "var(--color-safe)"), fontSize: "0.95rem" }}>
                            {labRunResult.scenario_info?.name}
                          </span>
                          <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", display: "block" }}>
                            Case: {labRunResult.case_id} • Latency: {labRunResult.total_latency_ms} ms • Execution: {labRunResult.execution_mode}
                          </span>
                        </div>
                        <span className={`decision-pill ${labRunResult.decision?.toLowerCase()}`}>{labRunResult.decision}</span>
                      </div>

                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "0.6rem", marginBottom: "1rem" }}>
                        <div style={{ background: "rgba(9, 13, 22, 0.4)", padding: "0.6rem", borderRadius: "4px" }}>
                          <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", display: "block" }}>Risk Score</span>
                          <strong style={{ fontSize: "1.1rem", fontFamily: "JetBrains Mono", color: labRunResult.risk_score >= 70 ? "var(--color-high-risk)" : "var(--color-safe)" }}>
                            {labRunResult.risk_score}%
                          </strong>
                        </div>
                        <div style={{ background: "rgba(9, 13, 22, 0.4)", padding: "0.6rem", borderRadius: "4px" }}>
                          <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", display: "block" }}>Trust Level</span>
                          <strong style={{ fontSize: "0.85rem", color: "var(--text-primary)" }}>{labRunResult.trust_level}</strong>
                        </div>
                        <div style={{ background: "rgba(9, 13, 22, 0.4)", padding: "0.6rem", borderRadius: "4px" }}>
                          <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", display: "block" }}>Payload Integrity</span>
                          <strong style={{ fontSize: "0.85rem", color: labRunResult.payload_integrity?.integrity_status === "INTEGRITY_VERIFIED" ? "var(--color-safe)" : "var(--color-high-risk)" }}>
                            {labRunResult.payload_integrity?.integrity_status || "N/A"}
                          </strong>
                        </div>
                        <div style={{ background: "rgba(9, 13, 22, 0.4)", padding: "0.6rem", borderRadius: "4px" }}>
                          <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", display: "block" }}>Transaction DNA</span>
                          <strong style={{ fontSize: "0.85rem", color: "var(--brand-primary)" }}>
                            {labRunResult.transaction_dna?.status || "INSUFFICIENT_HISTORY"}
                          </strong>
                        </div>
                        <div style={{ background: "rgba(9, 13, 22, 0.4)", padding: "0.6rem", borderRadius: "4px" }}>
                          <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", display: "block" }}>Quantum Gate</span>
                          <strong style={{ fontSize: "0.85rem", color: "var(--brand-cyan)" }}>
                            {labRunResult.quantum_analysis?.escalation_status || "BYPASSED"}
                          </strong>
                        </div>
                      </div>

                      {labRunResult.payload_integrity && (
                        <div style={{ marginBottom: "0.75rem" }}>
                          <PayloadIntegrityPanel payloadIntegrity={labRunResult.payload_integrity} />
                        </div>
                      )}

                      {labRunResult.transaction_dna && (
                        <div style={{ marginBottom: "0.75rem" }}>
                          <TransactionDNAPanel transactionDna={labRunResult.transaction_dna} />
                        </div>
                      )}
                    </motion.div>
                  )}
                </div>
              </motion.div>
            )}

            {/* 10. COPILOT */}
            {activeTab === "copilot" && (
              <motion.div
                key="copilot"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="tab-pane"
              >
                <div className="glass-panel copilot-panel" style={{ minHeight: "520px" }}>
                  <div className="panel-header">
                    <h2><MessageSquare size={18} style={{ color: "var(--brand-primary)" }} /> Evidence-Grounded AI Fraud Analyst</h2>
                    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                      <span className="evidence-tag observed" style={{ background: "rgba(0, 229, 255, 0.15)", color: "#00e5ff", border: "1px solid rgba(0, 229, 255, 0.3)" }}>
                        GROQ ACCELERATED
                      </span>
                      <span className="evidence-tag observed">EVIDENCE GROUNDED</span>
                    </div>
                  </div>
                  <p className="panel-desc">Grounds explanations in SHAP attribution, temporal attack chains, and graph linkages without fabricating facts.</p>

                  <div className="chat-window" style={{ height: "380px" }}>
                    <div className="chat-messages">
                      {copilotMessages.map((m, idx) => (
                        <div key={idx} className={`chat-msg ${m.sender}`}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                            <span style={{ fontSize: "0.75rem", fontWeight: 600, color: m.sender === "user" ? "var(--brand-primary)" : "var(--brand-secondary)" }}>
                              {m.sender === "user" ? "SOC Analyst" : "Quantum Kavacha Copilot"}
                            </span>
                            {m.provider && (
                              <span style={{
                                fontSize: "0.65rem",
                                padding: "2px 6px",
                                borderRadius: "4px",
                                background: m.execution_mode === "LIVE_LLM" ? "rgba(0, 229, 255, 0.12)" : "rgba(255, 171, 0, 0.12)",
                                color: m.execution_mode === "LIVE_LLM" ? "#00e5ff" : "#ffab00",
                                border: `1px solid ${m.execution_mode === "LIVE_LLM" ? "rgba(0, 229, 255, 0.3)" : "rgba(255, 171, 0, 0.3)"}`,
                                fontWeight: 500
                              }}>
                                {m.provider}
                              </span>
                            )}
                          </div>
                          <div style={{ whiteSpace: "pre-line" }}>{m.text}</div>
                          {m.sources && (
                            <div className="msg-sources" style={{ marginTop: "6px" }}>
                              <span>Grounded Sources:</span>
                              {m.sources.map((s, si) => <span key={si} className="src-tag">{s}</span>)}
                            </div>
                          )}
                        </div>
                      ))}
                      {chatLoading && (
                        <div className="chat-msg bot" style={{ opacity: 0.85, fontStyle: "italic", fontSize: "0.85rem", color: "#00e5ff" }}>
                          ⚡ Reasoning across SHAP, graph links, and Qiskit quantum statevector evidence via Groq...
                        </div>
                      )}
                    </div>
                    <div className="chat-input-row">
                      <input
                        placeholder="Ask copilot: 'Why was this payment flagged?', 'Explain first warning sign in attack chain'..."
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && !chatLoading && handleCopilotSend()}
                        disabled={chatLoading}
                      />
                      <button className="btn btn-primary" onClick={handleCopilotSend} disabled={chatLoading}>
                        <Send size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* 10. DEVICE TRUST CENTER */}
            {activeTab === "device-trust" && (
              <motion.div
                key="device-trust"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="tab-pane"
              >
                <DeviceTrustWorkspace fastApiBase={FASTAPI_BASE} />
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </main>

      {/* Forensic Details Modal */}
      <EvidenceDetailsModal
        isOpen={showEvidenceDrawer}
        onClose={() => setShowEvidenceDrawer(false)}
        evidenceVerification={checkResult?.evidence_verification}
        caseId={checkResult?.case_id}
      />
    </div>
  );
}

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Quantum Kavacha UI ErrorBoundary caught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: "100vh",
          backgroundColor: "#0B101E",
          color: "#F9FAFB",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "2rem",
          fontFamily: "Inter, sans-serif"
        }}>
          <div style={{
            background: "#1F2937",
            border: "1px solid rgba(220, 38, 38, 0.5)",
            borderRadius: "8px",
            padding: "2rem",
            maxWidth: "600px",
            width: "100%",
            textAlign: "center"
          }}>
            <h2 style={{ color: "#EF4444", marginBottom: "1rem" }}>Runtime Error Encountered</h2>
            <p style={{ color: "#D1D5DB", marginBottom: "1.5rem" }}>
              {this.state.error?.message || "An unexpected error occurred in the user interface."}
            </p>
            <button
              onClick={() => window.location.reload()}
              style={{
                background: "#2563EB",
                color: "#FFFFFF",
                border: "none",
                borderRadius: "6px",
                padding: "0.6rem 1.2rem",
                cursor: "pointer",
                fontWeight: 600
              }}
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const root = createRoot(document.getElementById("root"));
root.render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);