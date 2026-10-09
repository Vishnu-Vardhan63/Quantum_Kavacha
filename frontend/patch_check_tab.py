import re

with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# First, add the import at the top
import_statement = "import { TransactionsWorkspace } from './components/TransactionsWorkspace';\n"
if "TransactionsWorkspace" not in content:
    # insert after the last import
    last_import = content.rfind("import ")
    end_of_last_import = content.find("\n", last_import) + 1
    content = content[:end_of_last_import] + import_statement + content[end_of_last_import:]

# Now replace the check tab content
replacement = '''                {/* 1. TRANSACTIONS */}
                <TransactionsWorkspace 
                  fastApiBase={FASTAPI_BASE} 
                  onSelectTransaction={(txn_id) => {
                    setActiveCaseId(txn_id);
                    loadCaseDetails(txn_id);
                    setActiveTab("investigation");
                  }} 
                />'''

pattern = re.compile(r'\{/\* 1\. CHECK A PAYMENT \*/\}.*?(?=\{/\* 2\. RISK DASHBOARD \*/\}|{/\* 3\. INVESTIGATION CENTER \*/\}|{/\* 2\. OPERATIONS DASHBOARD \*/\}|{/\* 3\. INVESTIGATIONS \*/\}|{/\* 2\. OVERVIEW \*/\}|{/\* 1\. TRANSACTIONS \*/\}|{activeTab === "overview" &&)', re.DOTALL)
match = pattern.search(content)

if match:
    new_content = content[:match.start()] + replacement + '\n\n              ' + content[match.end():]
    with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced!")
else:
    print("Not found.")
