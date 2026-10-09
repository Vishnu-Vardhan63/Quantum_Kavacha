import re

with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

new_sidebar = '''          <div className="sidebar-nav-container">
            {/* Overview */}
            <div>
              <div className="sidebar-section-label">Overview</div>
              <div className="sidebar-nav-list">
                <button
                  className={sidebar-nav-item }
                  onClick={() => setActiveTab("overview")}
                >
                  <Activity size={16} /> Operations Dashboard
                </button>
              </div>
            </div>

            {/* Detection */}
            <div>
              <div className="sidebar-section-label">Detection</div>
              <div className="sidebar-nav-list">
                <button
                  className={sidebar-nav-item }
                  onClick={() => setActiveTab("check")}
                >
                  <FileSearch size={16} /> Transactions
                </button>
                <button
                  className={sidebar-nav-item }
                  onClick={() => setActiveTab("response")}
                >
                  <ShieldAlert size={16} /> Fraud Alerts
                </button>
                <button
                  className={sidebar-nav-item }
                  onClick={() => setActiveTab("investigation")}
                >
                  <Shield size={16} /> Investigations
                </button>
              </div>
            </div>

            {/* Intelligence */}
            <div>
              <div className="sidebar-section-label">Intelligence</div>
              <div className="sidebar-nav-list">
                <button
                  className={sidebar-nav-item }
                  onClick={() => setActiveTab("explain")}
                >
                  <Layers size={16} /> FraudDNA & Explain
                </button>
                <button
                  className={sidebar-nav-item }
                  onClick={() => { setActiveTab("graph"); loadCaseGraph(activeCaseId); }}
                >
                  <Network size={16} /> Entity Graph
                </button>
                <button
                  className={sidebar-nav-item }
                  onClick={() => setActiveTab("chain")}
                >
                  <GitFork size={16} /> Attack Chain
                </button>
                <button
                  className={sidebar-nav-item }
                  onClick={() => setActiveTab("models")}
                >
                  <Cpu size={16} /> Model Intelligence
                </button>
                <button
                  className={sidebar-nav-item }
                  onClick={() => setActiveTab("device-trust")}
                >
                  <Cpu size={16} /> Device Trust
                </button>
              </div>
            </div>

            {/* Simulation & Assistance */}
            <div>
              <div className="sidebar-section-label">Simulation & Assistance</div>
              <div className="sidebar-nav-list">
                <button
                  className={sidebar-nav-item }
                  onClick={() => setActiveTab("attack-lab")}
                >
                  <Flame size={16} /> Attack Lab
                </button>
                <button
                  className={sidebar-nav-item }
                  onClick={() => setActiveTab("copilot")}
                >
                  <MessageSquare size={16} /> Q-Fraud Copilot
                </button>
              </div>
            </div>
          </div>'''

# Regex to match the sidebar-nav-container div
pattern = re.compile(r'<div className="sidebar-nav-container">.*?</div>\s*</div>\s*</div>', re.DOTALL)
# Wait, the end of sidebar-nav-container is just before {/* Sidebar Footer */}
pattern2 = re.compile(r'<div className="sidebar-nav-container">.*?{/\* Sidebar Footer \*/}', re.DOTALL)
match = pattern2.search(content)

if match:
    new_content = content[:match.start()] + new_sidebar + '\n\n          {/* Sidebar Footer */}' + content[match.end():]
    with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced!")
else:
    print("Not found.")
