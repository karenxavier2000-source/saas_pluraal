path = r'C:\Users\karen.xavier\Desktop\pluraal saas\Backend\services\delegation_service.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old = 'if user["hierarquia"] == "Master":'
new = 'if user["hierarquia"] in ("Master", "Administrador"):'
if old in text:
    text = text.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated get_effective_user_scope")
else:
    print("Not found")

old2 = 'if hierarquia == "Master":'
new2 = 'if hierarquia in ("Master", "Administrador"):'
if old2 in text:
    text = text.replace(old2, new2)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated compute_effective_scope_from_access_list")
