path = r'C:\Users\karen.xavier\Desktop\pluraal saas\Backend\services\auth_service.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old = '''            "pode_criar_usuario": user["pode_criar_usuario"],
            "paginas_permitidas": user.get("paginas_permitidas") or []'''

new = '''            "pode_criar_usuario": user["pode_criar_usuario"],
            "pode_simular_visao": bool(user.get("pode_simular_visao")),
            "limite_criacao_usuarios": user.get("limite_criacao_usuarios"),
            "paginas_permitidas": user.get("paginas_permitidas") or []'''

if old in text:
    text = text.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('auth_service.py updated.')
else:
    print('old not found')
