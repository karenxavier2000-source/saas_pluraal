import sys
import re

path = r'C:\Users\karen.xavier\Desktop\pluraal saas\Backend\services\user_service.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

check_limit_code = '''        # Check user creation limit
        cur.execute("SELECT limite_criacao_usuarios FROM pluraal.usuario WHERE id_usuario = %s", (creator_id,))
        creator_limit_row = cur.fetchone()
        if creator_limit_row and creator_limit_row.get("limite_criacao_usuarios") is not None:
            cur.execute("SELECT COUNT(*) as total FROM pluraal.usuario WHERE criado_por_usuario_id = %s", (creator_id,))
            created_count = cur.fetchone()["total"]
            if created_count >= creator_limit_row["limite_criacao_usuarios"]:
                raise PermissionError("Você atingiu o limite máximo de usuários que pode criar.")

        check_delegation_rules('''

if 'creator_limit_row' not in text:
    text = re.sub(r'\s+check_delegation_rules\(', '\n' + check_limit_code, text, count=1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Limit enforcement added.')
else:
    print('Already added.')
