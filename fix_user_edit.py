import sys
import re

# 1. Update users.js canEdit
path_users = r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend\js\users.js'
with open(path_users, 'r', encoding='utf-8') as f:
    text_users = f.read()

old_edit = '''const canEdit = isMaster || (u.criado_por_usuario_id === currentLoggedUser.id_usuario) || (u.id_usuario === currentLoggedUser.id_usuario);'''
new_edit = '''const canEdit = isMaster || (u.criado_por_usuario_id === currentLoggedUser.id_usuario); // Restringido: não-master não pode editar a si mesmo'''
if old_edit in text_users:
    text_users = text_users.replace(old_edit, new_edit)
    with open(path_users, 'w', encoding='utf-8') as f:
        f.write(text_users)
    print('Updated users.js')
else:
    print('old_edit not found in users.js')

# Also update user_service.py just to be safe
path_user_srv = r'C:\Users\karen.xavier\Desktop\pluraal saas\Backend\services\user_service.py'
with open(path_user_srv, 'r', encoding='utf-8') as f:
    text_srv = f.read()
old_srv_edit = '''        if updater_id == target_id and not is_master:
            if hierarquia != target_user["hierarquia"]:
                raise PermissionError("VocǦ nǜo tem permissǜo para alterar sua prpria hierarquia.")
            if pode_criar_usuario != target_user["pode_criar_usuario"]:
                raise PermissionError("VocǦ nǜo tem permissǜo para alterar sua prpria permissǜo de criar usuǭrios.")'''
# Encoding issues mean we should use regex for user_service.py
new_srv_edit = '''        if updater_id == target_id and not is_master:
            raise PermissionError("Usuários não-master não podem editar seu próprio perfil.")'''
text_srv = re.sub(r'if updater_id == target_id and not is_master:.*?raise PermissionError.*?raise PermissionError[^)]*\)', new_srv_edit, text_srv, flags=re.DOTALL)
with open(path_user_srv, 'w', encoding='utf-8') as f:
    f.write(text_srv)
print('Updated user_service.py')


# 2. Update index.html to add profileSchoolList
path_index = r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html'
with open(path_index, 'r', encoding='utf-8', errors='ignore') as f:
    text_index = f.read()
# Let's find <strong id="profileSchoolCount"></strong></div></div>
# and append <div id="profileSchoolList" ...></div>
if 'id="profileSchoolList"' not in text_index:
    text_index = re.sub(
        r'(<strong id="profileSchoolCount">.*?</strong></div></div>)',
        r'\1\n          <div id="profileSchoolList" style="margin-top:1rem; max-height:250px; overflow-y:auto; font-size:0.85rem; border:1px solid var(--border-color); border-radius:8px; padding:0.5rem; display:none; background:var(--bg-card);"></div>',
        text_index
    )
    with open(path_index, 'w', encoding='utf-8') as f:
        f.write(text_index)
    print('Updated index.html')
else:
    print('profileSchoolList already in index.html')


# 3. Update profile.js to populate profileSchoolList
path_profile = r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend\js\profile.js'
with open(path_profile, 'r', encoding='utf-8', errors='ignore') as f:
    text_profile = f.read()

profile_logic = '''      document.getElementById('profileSchoolCount').textContent = this.options.entidades.length.toLocaleString('pt-BR');
      
      const schoolList = document.getElementById('profileSchoolList');
      if (schoolList && this.options.entidades.length > 0) {
        schoolList.style.display = 'block';
        
        // Agrupar por Uniao -> Associacao -> Escola
        const tree = {};
        this.options.entidades.forEach(e => {
            const u = e.uniao || 'Sem União';
            const a = e.associacao || 'Sem Associação';
            const s = e.escola;
            
            if (!tree[u]) tree[u] = {};
            if (!tree[u][a]) tree[u][a] = [];
            if (s) tree[u][a].push(s);
        });
        
        let html = '<ul style="list-style:none; padding:0; margin:0;">';
        for (const uniao of Object.keys(tree).sort()) {
            html += <li style="font-weight:bold; margin-top:0.5rem; color:var(--color-primary);"></li>;
            html += '<ul style="list-style:none; padding-left:1rem; margin:0;">';
            for (const assoc of Object.keys(tree[uniao]).sort()) {
                html += <li style="font-weight:600; margin-top:0.25rem; color:var(--text-main);"></li>;
                const escolas = tree[uniao][assoc].sort();
                if (escolas.length > 0) {
                    html += '<ul style="list-style:disc; padding-left:1.5rem; margin:0; color:var(--text-muted);">';
                    escolas.forEach(esc => {
                        html += <li></li>;
                    });
                    html += '</ul>';
                }
            }
            html += '</ul>';
        }
        html += '</ul>';
        schoolList.innerHTML = html;
      } else if (schoolList) {
        schoolList.style.display = 'none';
      }
'''

text_profile = re.sub(r'document\.getElementById\(\'profileSchoolCount\'\)\.textContent.*?;', profile_logic, text_profile)
with open(path_profile, 'w', encoding='utf-8') as f:
    f.write(text_profile)
print('Updated profile.js')
