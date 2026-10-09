with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

import_statement = "import { FraudAlertsWorkspace } from './components/FraudAlertsWorkspace';\n"
if "FraudAlertsWorkspace" not in content:
    last_import = content.rfind("import ")
    end_of_last_import = content.find("\n", last_import) + 1
    content = content[:end_of_last_import] + import_statement + content[end_of_last_import:]
    with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/main.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added import!")
else:
    print("Already there.")
