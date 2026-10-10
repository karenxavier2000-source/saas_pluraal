with open(r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

old_btn = '''        <button type="submit" id="barrierSubmitBtn" class="btn btn-primary w-full" style="padding: 0.75rem; margin-top: 0.5rem;">
          <span>Confirmar Nova Senha</span>
        </button>'''

new_btn = '''        <button type="submit" id="barrierSubmitBtn" class="btn btn-primary w-full" style="padding: 0.75rem; margin-top: 0.5rem;">
          <span>Confirmar Nova Senha</span>
        </button>
        <button type="button" class="btn btn-outline w-full" onclick="Auth.logout()" style="padding: 0.75rem; margin-top: 0.5rem;">
          <span>Sair da Conta</span>
        </button>'''

if old_btn in text:
    text = text.replace(old_btn, new_btn)
    with open(r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Button added successfully.')
else:
    print('Could not find exact button string.')
