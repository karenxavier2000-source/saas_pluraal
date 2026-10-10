path = r'c:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_simular = '''              <label id="podeSimularContainer" style="display:none; align-items:center; gap:0.5rem; cursor:pointer; margin-top: 0.75rem; border-top: 1px solid var(--border-color); padding-top: 0.75rem;">
                <input type="checkbox" id="formUserPodeSimular" style="width:16px; height:16px;">
                <div style="display:flex; flex-direction:column;">
                  <span class="text-sm font-semibold text-main">Permitir simular visão de usuário</span>
                </div>
              </label>'''

new_simular = '''              <label id="podeSimularContainer" style="display:none; align-items:center; gap:0.5rem; cursor:pointer; margin-top: 0.75rem; border-top: 1px solid var(--border-color); padding-top: 0.75rem;">
                <input type="checkbox" id="formUserPodeSimular" style="width:16px; height:16px;">
                <div style="display:flex; flex-direction:column;">
                  <span class="text-sm font-semibold text-main">Permitir simular visão de usuário</span>
                </div>
              </label>
              <label id="podeCadastrarEscolaContainer" style="display:none; align-items:center; gap:0.5rem; cursor:pointer; margin-top: 0.75rem; border-top: 1px solid var(--border-color); padding-top: 0.75rem;">
                <input type="checkbox" id="formUserPodeCadastrarEscola" style="width:16px; height:16px;">
                <div style="display:flex; flex-direction:column;">
                  <span class="text-sm font-semibold text-main">Permitir cadastrar escolas no banco de escolas</span>
                </div>
              </label>'''

content = content.replace(old_simular, new_simular)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated index.html modal')
