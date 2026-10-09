import re

with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

import_statement = "import { FraudAlertsWorkspace } from './components/FraudAlertsWorkspace';\n"
if "FraudAlertsWorkspace" not in content:
    last_import = content.rfind("import ")
    end_of_last_import = content.find("\n", last_import) + 1
    content = content[:end_of_last_import] + import_statement + content[end_of_last_import:]

replacement = '''              {/* 5. FRAUD ALERTS (formerly response) */}
              {activeTab === "response" && (
                <motion.div
                  key="response"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.15 }}
                  className="tab-pane"
                >
                  <FraudAlertsWorkspace
                    fastApiBase={FASTAPI_BASE}
                    onSelectAlert={(txn_id) => {
                      setActiveCaseId(txn_id);
                      loadCaseDetails(txn_id);
                      setActiveTab("investigation");
                    }}
                  />
                </motion.div>
              )}'''

# String replacement
target = '''            {/* 5. RESPONSE CENTER */}
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
                  currentCaseId={activeCaseId || activeCase?.case_id || "QF-20261007-49910"}
                  onNavigateTab={(tab) => setActiveTab(tab)}
                  onAskCopilot={(prompt) => handleAskCopilot(prompt)}
                />
              </motion.div>
            )}'''
            
# Let's use regex without exact spacing matching.
pattern = re.compile(r'\{/\* 5\. RESPONSE CENTER \*/\}.*?<ResponseCenterWorkspace.*?\/>\s*<\/motion\.div>\s*\}', re.DOTALL)
match = pattern.search(content)

if match:
    new_content = content[:match.start()] + replacement + content[match.end():]
    with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced!")
else:
    print("Not found.")
