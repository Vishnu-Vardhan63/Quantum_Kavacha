import re

with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''          {/* Page Header */}
          <div className="page-header" style={{ padding: "1.5rem", borderBottom: "1px solid var(--border-subtle)", display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--bg-header)", backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 10 }}>
            <h1 style={{ fontSize: "1.4rem", fontWeight: 700, margin: 0, textTransform: "capitalize", color: "var(--text-primary)" }}>
              {activeTab.replace('-', ' ')}
            </h1>
            <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                {activeTab === "check" && <span className="evidence-tag observed">Live Processing</span>}
                <span className="status-dot-indicator" style={{ background: "rgba(16, 185, 129, 0.1)", color: "var(--color-safe)", padding: "0.4rem 0.8rem", borderRadius: "var(--radius-md)", fontSize: "0.75rem", fontWeight: 600 }}>
                  <span className="status-dot"></span> SYSTEMS NOMINAL
                </span>
            </div>
          </div>'''

pattern = re.compile(r'<div className="journey-bar">.*?</div>\s*<AnimatePresence mode="wait">', re.DOTALL)
match = pattern.search(content)

if match:
    new_content = content[:match.start()] + replacement + '\n\n          <AnimatePresence mode="wait">' + content[match.end():]
    with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced!")
else:
    print("Not found.")
