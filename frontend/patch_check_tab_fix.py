import re

with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''              {/* 1. TRANSACTIONS */}
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
              )}'''

pattern = re.compile(r'\{/\* 1\. TRANSACTIONS \*/\}.*?<TransactionsWorkspace[^>]*/>', re.DOTALL)
match = pattern.search(content)

if match:
    new_content = content[:match.start()] + replacement + content[match.end():]
    with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced!")
else:
    print("Not found.")
