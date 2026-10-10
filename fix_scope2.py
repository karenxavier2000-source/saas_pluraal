path = r'C:\Users\karen.xavier\Desktop\pluraal saas\Backend\services\delegation_service.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = re.sub(r'if user_info\["hierarquia"\] == "Master":', 'if user_info["hierarquia"] in ("Master", "Administrador"):', text)
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated")
