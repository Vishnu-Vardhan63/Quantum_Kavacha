import re

with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''                {/* Enterprise Operations Dashboard */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "1.25rem" }}>
                  <div className="glass-panel" style={{ background: "var(--bg-surface-elevated)" }}>
                    <div className="panel-header">
                      <h2><Activity size={18} style={{ color: "var(--brand-primary)" }} /> Operations Dashboard</h2>
                      {health ? (
                        <span className="evidence-tag observed">CONNECTED</span>
                      ) : (
                        <span className="evidence-tag critical">DISCONNECTED</span>
                      )}
                    </div>
                    <p className="panel-desc">
                      Live transaction telemetry and processing metrics.
                    </p>
                    
                    <div className="kpi-mini-grid" style={{ marginTop: "1rem", display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem" }}>
                      <div className="kpi-mini" style={{ padding: "1rem", background: "rgba(255,255,255,0.03)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Processed Transactions</span>
                        <strong style={{ fontSize: "1.5rem", color: "var(--text-primary)", display: "block", marginTop: "0.5rem" }}>{analytics?.total_transactions !== undefined ? analytics.total_transactions : "UNAVAILABLE"}</strong>
                      </div>
                      <div className="kpi-mini" style={{ padding: "1rem", background: "var(--color-critical-subtle)", borderRadius: "var(--radius-md)", border: "1px solid var(--color-critical-border)" }}>
                        <span style={{ fontSize: "0.7rem", color: "var(--color-critical)", textTransform: "uppercase" }}>Confirmed Fraud</span>
                        <strong style={{ fontSize: "1.5rem", color: "var(--color-critical)", display: "block", marginTop: "0.5rem" }}>{analytics?.fraud_detected !== undefined ? analytics.fraud_detected : "UNAVAILABLE"}</strong>
                      </div>
                      <div className="kpi-mini" style={{ padding: "1rem", background: "var(--color-caution-subtle)", borderRadius: "var(--radius-md)", border: "1px solid var(--color-caution-border)" }}>
                        <span style={{ fontSize: "0.7rem", color: "var(--color-caution)", textTransform: "uppercase" }}>Suspicious Escalations</span>
                        <strong style={{ fontSize: "1.5rem", color: "var(--color-caution)", display: "block", marginTop: "0.5rem" }}>{analytics?.suspicious_flagged !== undefined ? analytics.suspicious_flagged : "UNAVAILABLE"}</strong>
                      </div>
                      <div className="kpi-mini" style={{ padding: "1rem", background: "rgba(255,255,255,0.03)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Quantum Status</span>
                        <strong style={{ fontSize: "1.1rem", color: "var(--brand-cyan)", display: "block", marginTop: "0.5rem" }}>{health?.quantum_engine?.mode ?? "UNAVAILABLE"}</strong>
                      </div>
                    </div>
                  </div>'''

# Match from {/* 3D Quantum Core Hero Section */} up to just before {/* Live Threat Monitor Feed */}
pattern = re.compile(r'\{/\* 3D Quantum Core Hero Section \*/\}.*?(?=\{/\* Live Threat Monitor Feed \*/\})', re.DOTALL)
match = pattern.search(content)

if match:
    new_content = content[:match.start()] + replacement + '\n                  ' + content[match.end():]
    with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced!")
else:
    print("Not found.")
