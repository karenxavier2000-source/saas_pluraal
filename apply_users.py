import os
import re

path_js = r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend\js\users.js'
with open(path_js, 'r', encoding='utf-8') as f:
    js_content = f.read()

# 1. Hierarchy names
js_content = js_content.replace(
    '''const names = { 'Master': 'Master (Acesso Total)', 'uniao': 'Uniǜo', 'associacao': 'Associaǜo', 'escola': 'Escola' };''',
    '''const names = { 'Master': 'Master (Acesso Total)', 'Administrador': 'Administrador', 'uniao': 'União', 'associacao': 'Associação', 'escola': 'Escola' };'''
)
# The encoding got a bit messed up previously in users.js due to powershell, we'll fix it if we can
js_content = js_content.replace("'Uniǜo'", "'União'")
js_content = js_content.replace("'Associaǜo'", "'Associação'")

# 2. openEditUserModal bindings
js_content = js_content.replace(
    '''document.getElementById('formUserPodeCriar').checked = !!user.pode_criar_usuario;''',
    '''document.getElementById('formUserPodeCriar').checked = !!user.pode_criar_usuario;
      const chkPodeSimular = document.getElementById('formUserPodeSimular');
      if (chkPodeSimular) chkPodeSimular.checked = !!user.pode_simular_visao;
      const inpLimite = document.getElementById('formUserLimiteCriacao');
      if (inpLimite) inpLimite.value = user.limite_criacao_usuarios || '';'''
)

# 3. Handle toggles
# Inside setupHierarchyAndAccessSelectors or modal opening...
# Let's add an event listener to formUserPodeCriar
# We can inject it into setupHierarchyAndAccessSelectors
setup_old = '''const hierSelect = document.getElementById('formUserHierarchy');'''
setup_new = '''const chkCriar = document.getElementById('formUserPodeCriar');
      if (chkCriar) {
        chkCriar.addEventListener('change', (e) => {
          document.getElementById('limiteCriacaoContainer').style.display = e.target.checked ? 'block' : 'none';
        });
      }
      const hierSelect = document.getElementById('formUserHierarchy');'''
if setup_old in js_content and 'chkCriar.addEventListener' not in js_content:
    js_content = js_content.replace(setup_old, setup_new)

# openCreateUserModal bindings
create_old = '''document.getElementById('formUserPodeCriar').checked = false;'''
create_new = '''document.getElementById('formUserPodeCriar').checked = false;
      const chkPodeSimular = document.getElementById('formUserPodeSimular');
      if (chkPodeSimular) chkPodeSimular.checked = false;
      const inpLimite = document.getElementById('formUserLimiteCriacao');
      if (inpLimite) inpLimite.value = '';
      const limitCont = document.getElementById('limiteCriacaoContainer');
      if (limitCont) limitCont.style.display = 'none';'''
js_content = js_content.replace(create_old, create_new)

# In handleHierarchyChangeInForm (showing/hiding PodeCriarContainer and PodeSimularContainer)
# We need to make sure PodeSimularContainer is visible only if the current logged user is Master
# The current user's capabilities dictates it
handle_hier_old = '''const podeCriarContainer = document.getElementById('podeCriarContainer');
    if (this.capabilities.can_grant_pode_criar_usuario) {'''
handle_hier_new = '''const podeCriarContainer = document.getElementById('podeCriarContainer');
    const podeSimularContainer = document.getElementById('podeSimularContainer');
    if (podeSimularContainer) {
        podeSimularContainer.style.display = this.capabilities.can_grant_pode_simular ? 'flex' : 'none';
    }
    if (this.capabilities.can_grant_pode_criar_usuario) {'''
js_content = js_content.replace(handle_hier_old, handle_hier_new)

# handleSaveUser JSON payload
save_old = '''      pode_criar_usuario: pode_criar_usuario,
      acessos: this.selectedAccesses,
      paginas_permitidas: Array.from(document.querySelectorAll('input[name="userPages"]:checked')).map(cb => cb.value)
    };'''
save_new = '''      pode_criar_usuario: pode_criar_usuario,
      pode_simular_visao: document.getElementById('formUserPodeSimular') ? document.getElementById('formUserPodeSimular').checked : false,
      limite_criacao_usuarios: document.getElementById('formUserLimiteCriacao') ? document.getElementById('formUserLimiteCriacao').value : '',
      acessos: this.selectedAccesses,
      paginas_permitidas: Array.from(document.querySelectorAll('input[name="userPages"]:checked')).map(cb => cb.value)
    };'''
js_content = js_content.replace(save_old, save_new)

with open(path_js, 'w', encoding='utf-8') as f:
    f.write(js_content)

print('users.js updated.')
