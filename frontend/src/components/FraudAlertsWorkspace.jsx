import React, { useState, useEffect } from 'react';
import { Search, Filter, AlertTriangle, ShieldAlert } from 'lucide-react';
import { motion } from 'framer-motion';

export function FraudAlertsWorkspace({ fastApiBase, onSelectAlert }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${fastApiBase}/api/transactions?limit=100`)
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) {
            const flagged = data.filter(t => t.decision !== "ALLOW" && t.risk_score >= 35);
            setAlerts(flagged);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [fastApiBase]);

  return (
    <div className="glass-panel" style={{ minHeight: '600px', background: "var(--bg-surface-elevated)" }}>
      <div className="panel-header" style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
        <h2><ShieldAlert size={18} style={{ color: "var(--color-critical)" }} /> High-Priority Fraud Alerts</h2>
      </div>
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}>Loading alerts...</div>
      ) : alerts.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No open fraud alerts.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          {alerts.map((a, idx) => (
            <div
              key={idx}
              style={{
                background: "var(--bg-surface)",
                borderLeft: `3px solid ${a.risk_score >= 80 ? "var(--color-high-risk)" : "var(--color-caution)"}`,
                padding: "1rem",
                borderRadius: "0 var(--radius-md) var(--radius-md) 0",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                cursor: "pointer",
                boxShadow: "var(--shadow-sm)"
              }}
              onClick={() => onSelectAlert(a.txn_id)}
            >
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <AlertTriangle size={14} style={{ color: a.risk_score >= 80 ? "var(--color-high-risk)" : "var(--color-caution)" }} />
                  <span style={{ fontFamily: "JetBrains Mono", fontWeight: 700, color: "var(--text-primary)", fontSize: "0.9rem" }}>
                    {a.txn_id}
                  </span>
                  <span className={`decision-pill ${a.decision?.toLowerCase()}`}>
                    {a.decision}
                  </span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "4px" }}>
                  Amount: {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(a.amount || 0)} | {a.risk_factors?.join(", ") || "Multiple risk factors"}
                </div>
              </div>

              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "1.2rem", fontWeight: 800, color: a.risk_score >= 80 ? "var(--color-high-risk)" : "var(--color-caution)", fontFamily: "JetBrains Mono" }}>
                  {a.risk_score?.toFixed(1)}%
                </span>
                <span style={{ fontSize: "0.7rem", color: "var(--text-dim)", display: "block" }}>Risk Score</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
