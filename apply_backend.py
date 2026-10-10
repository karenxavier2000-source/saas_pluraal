import os

backend_dir = r'C:\Users\karen.xavier\Desktop\pluraal saas\Backend'
frontend_dir = r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend'

def replace_in_file(path, old, new):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# 1. user_service.py
path_user_service = os.path.join(backend_dir, 'services', 'user_service.py')
with open(path_user_service, 'r', encoding='utf-8') as f:
    us_content = f.read()

# Selects
us_content = us_content.replace('ativo, trocar_senha_no_primeiro_acesso, pode_criar_usuario,', 'ativo, trocar_senha_no_primeiro_acesso, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios,')
us_content = us_content.replace('u.ativo, u.trocar_senha_no_primeiro_acesso, u.pode_criar_usuario,', 'u.ativo, u.trocar_senha_no_primeiro_acesso, u.pode_criar_usuario, u.pode_simular_visao, u.limite_criacao_usuarios,')
us_content = us_content.replace('SELECT id_usuario, hierarquia, pode_criar_usuario, paginas_permitidas', 'SELECT id_usuario, hierarquia, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios, paginas_permitidas')
us_content = us_content.replace('SELECT id_usuario, hierarquia, pode_criar_usuario, criado_por_usuario_id, ativo, token_versao', 'SELECT id_usuario, hierarquia, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios, criado_por_usuario_id, ativo, token_versao')

# create_user assignments
create_assign_old = '''    pode_criar_usuario = user_data.get("pode_criar_usuario", False)
    acessos = user_data.get("acessos", [])'''
create_assign_new = '''    pode_criar_usuario = user_data.get("pode_criar_usuario", False)
    pode_simular_visao = user_data.get("pode_simular_visao", False)
    limite_criacao_usuarios = user_data.get("limite_criacao_usuarios")
    if limite_criacao_usuarios == '': limite_criacao_usuarios = None
    acessos = user_data.get("acessos", [])'''
us_content = us_content.replace(create_assign_old, create_assign_new)

# check_delegation_rules in create_user
check_del_old = '''            target_pode_criar_usuario=pode_criar_usuario,
            is_edit=False,
            cur=cur
        )'''
check_del_new = '''            target_pode_criar_usuario=pode_criar_usuario,
            target_pode_simular_visao=pode_simular_visao,
            is_edit=False,
            cur=cur
        )'''
us_content = us_content.replace(check_del_old, check_del_new)

# insert query
insert_old = '''            INSERT INTO pluraal.usuario (
                nome_completo_usuario, email, senha, hierarquia,
                ativo, trocar_senha_no_primeiro_acesso, pode_criar_usuario,
                criado_por_usuario_id, criado_em, token_versao, paginas_permitidas
            ) VALUES (
                %s, %s, %s, %s,
                %s, true, %s,
                %s, now(), 1, %s
            ) RETURNING id_usuario, criado_em;
        """, (nome, email, password_hash, hierarquia, ativo, pode_criar_usuario, creator_id, paginas_permitidas))'''
insert_new = '''            INSERT INTO pluraal.usuario (
                nome_completo_usuario, email, senha, hierarquia,
                ativo, trocar_senha_no_primeiro_acesso, pode_criar_usuario,
                pode_simular_visao, limite_criacao_usuarios,
                criado_por_usuario_id, criado_em, token_versao, paginas_permitidas
            ) VALUES (
                %s, %s, %s, %s,
                %s, true, %s,
                %s, %s,
                %s, now(), 1, %s
            ) RETURNING id_usuario, criado_em;
        """, (nome, email, password_hash, hierarquia, ativo, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios, creator_id, paginas_permitidas))'''
us_content = us_content.replace(insert_old, insert_new)

# return create
ret_create_old = '''            "pode_criar_usuario": pode_criar_usuario,
            "senha_temporaria": temp_password  # Displayed ONLY ONCE
        }'''
ret_create_new = '''            "pode_criar_usuario": pode_criar_usuario,
            "pode_simular_visao": pode_simular_visao,
            "limite_criacao_usuarios": limite_criacao_usuarios,
            "senha_temporaria": temp_password  # Displayed ONLY ONCE
        }'''
us_content = us_content.replace(ret_create_old, ret_create_new)

# update_user assignments
update_assign_old = '''    pode_criar_usuario = update_data.get("pode_criar_usuario", False)
    acessos = update_data.get("acessos", [])'''
update_assign_new = '''    pode_criar_usuario = update_data.get("pode_criar_usuario", False)
    pode_simular_visao = update_data.get("pode_simular_visao", False)
    limite_criacao_usuarios = update_data.get("limite_criacao_usuarios")
    if limite_criacao_usuarios == '': limite_criacao_usuarios = None
    acessos = update_data.get("acessos", [])'''
us_content = us_content.replace(update_assign_old, update_assign_new)

# check_delegation_rules in update_user
check_up_old = '''            target_pode_criar_usuario=pode_criar_usuario,
            is_edit=True,
            target_user_id=target_id,
            cur=cur
        )'''
check_up_new = '''            target_pode_criar_usuario=pode_criar_usuario,
            target_pode_simular_visao=pode_simular_visao,
            is_edit=True,
            target_user_id=target_id,
            cur=cur
        )'''
us_content = us_content.replace(check_up_old, check_up_new)

# update query
up_query_old = '''                pode_criar_usuario = %s,
                token_versao = %s,
                paginas_permitidas = %s
            WHERE id_usuario = %s;
        """, (nome, email, hierarquia, ativo, pode_criar_usuario, new_token_versao, paginas_permitidas, target_id))'''
up_query_new = '''                pode_criar_usuario = %s,
                pode_simular_visao = %s,
                limite_criacao_usuarios = %s,
                token_versao = %s,
                paginas_permitidas = %s
            WHERE id_usuario = %s;
        """, (nome, email, hierarquia, ativo, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios, new_token_versao, paginas_permitidas, target_id))'''
us_content = us_content.replace(up_query_old, up_query_new)

with open(path_user_service, 'w', encoding='utf-8') as f:
    f.write(us_content)


# 2. delegation_service.py
path_del = os.path.join(backend_dir, 'services', 'delegation_service.py')
with open(path_del, 'r', encoding='utf-8') as f:
    del_content = f.read()

get_scope_old = '''        SELECT hierarquia, pode_criar_usuario, paginas_permitidas
        FROM pluraal.usuario
        WHERE id_usuario = %s'''
get_scope_new = '''        SELECT hierarquia, pode_criar_usuario, paginas_permitidas, pode_simular_visao, limite_criacao_usuarios
        FROM pluraal.usuario
        WHERE id_usuario = %s'''
del_content = del_content.replace(get_scope_old, get_scope_new)

dict_scope_old = '''        "pode_criar_usuario": bool(user_info["pode_criar_usuario"]),
        "paginas_permitidas": user_info["paginas_permitidas"] or [],
        "unioes": set(),'''
dict_scope_new = '''        "pode_criar_usuario": bool(user_info["pode_criar_usuario"]),
        "pode_simular_visao": bool(user_info["pode_simular_visao"]),
        "limite_criacao_usuarios": user_info["limite_criacao_usuarios"],
        "paginas_permitidas": user_info["paginas_permitidas"] or [],
        "unioes": set(),'''
del_content = del_content.replace(dict_scope_old, dict_scope_new)

# check_delegation_rules definition
check_def_old = '''def check_delegation_rules(creator_user_id: int, target_hierarquia: str, accesses_to_grant: list, target_pode_criar_usuario: bool, is_edit: bool, cur, target_user_id: int = None):'''
check_def_new = '''def check_delegation_rules(creator_user_id: int, target_hierarquia: str, accesses_to_grant: list, target_pode_criar_usuario: bool, target_pode_simular_visao: bool, is_edit: bool, cur, target_user_id: int = None):'''
del_content = del_content.replace(check_def_old, check_def_new)

# Inside check_delegation_rules
check_logic_old = '''    if target_pode_criar_usuario and not creator_scope["pode_criar_usuario"] and creator_scope["hierarquia"] != "Master":
        raise PermissionError("VocǦ nǜo tem permissǜo para delegar a criaǜo de usuǭrios.")'''
check_logic_new = '''    if target_pode_criar_usuario and not creator_scope["pode_criar_usuario"] and creator_scope["hierarquia"] != "Master":
        raise PermissionError("VocǦ nǜo tem permissǜo para delegar a criaǜo de usuǭrios.")
    
    if target_pode_simular_visao and creator_scope["hierarquia"] != "Master":
        raise PermissionError("Apenas o Master pode liberar a simulaǜo de vises para outros usuǭrios.")
    
    # Administrador rules
    if target_hierarquia == "Administrador" and creator_scope["hierarquia"] != "Master":
        raise PermissionError("Apenas o Master pode criar usuǭrios Administradores.")'''
# Notice the text was broken before. We can append before     valid_target_hierarchies
del_content = del_content.replace(
'''    valid_target_hierarchies = {
        "Master": ["Master", "uniao", "associacao", "escola"],''',
'''    if target_pode_simular_visao and creator_scope["hierarquia"] != "Master":
        raise PermissionError("Apenas o Master pode liberar a simulação de visões para outros usuários.")
    if target_hierarquia == "Administrador" and creator_scope["hierarquia"] != "Master":
        raise PermissionError("Apenas o Master pode criar usuários Administradores.")

    valid_target_hierarchies = {
        "Master": ["Master", "Administrador", "uniao", "associacao", "escola"],
        "Administrador": ["Administrador", "uniao", "associacao", "escola"],'''
)
with open(path_del, 'w', encoding='utf-8') as f:
    f.write(del_content)


# 3. hierarchy_service.py
path_hier = os.path.join(backend_dir, 'services', 'hierarchy_service.py')
with open(path_hier, 'r', encoding='utf-8') as f:
    hier_content = f.read()

hier_dict_old = '''        allowed_hierarchies = {
            "Master": ["Master", "uniao", "associacao", "escola"],
            "uniao": ["uniao", "associacao", "escola"],
            "associacao": ["associacao", "escola"],
            "escola": ["escola"]
        }.get(h, [])'''
hier_dict_new = '''        allowed_hierarchies = {
            "Master": ["Master", "Administrador", "uniao", "associacao", "escola"],
            "Administrador": ["Administrador", "uniao", "associacao", "escola"],
            "uniao": ["uniao", "associacao", "escola"],
            "associacao": ["associacao", "escola"],
            "escola": ["escola"]
        }.get(h, [])'''
hier_content = hier_content.replace(hier_dict_old, hier_dict_new)

hier_ret_old = '''            "can_grant_pode_criar_usuario": can_manage_pode_criar,
            "allowed_target_hierarchies": allowed_hierarchies,'''
hier_ret_new = '''            "can_grant_pode_criar_usuario": can_manage_pode_criar,
            "can_grant_pode_simular": (h == "Master"),
            "allowed_target_hierarchies": allowed_hierarchies,'''
hier_content = hier_content.replace(hier_ret_old, hier_ret_new)

with open(path_hier, 'w', encoding='utf-8') as f:
    f.write(hier_content)


# 4. index.html
path_index = os.path.join(frontend_dir, 'index.html')
with open(path_index, 'r', encoding='utf-8', errors='ignore') as f:
    idx_content = f.read()

idx_pode_criar_old = '''          <div id="podeCriarContainer" class="form-group hidden" style="margin-top: 0.5rem; padding: 0.75rem; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px;">
            <label style="display:flex; align-items:center; gap:0.5rem; cursor:pointer;">
              <input type="checkbox" id="formUserPodeCriar" style="width:16px; height:16px;">
              <div style="display:flex; flex-direction:column;">
                <span class="text-sm font-semibold text-main">Permitir criar e gerenciar usuǭrios</span>
              </div>
            </label>
          </div>'''
          
idx_pode_criar_new = '''          <div id="podeCriarContainer" class="form-group hidden" style="margin-top: 0.5rem; padding: 0.75rem; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px;">
            <label style="display:flex; align-items:center; gap:0.5rem; cursor:pointer;">
              <input type="checkbox" id="formUserPodeCriar" style="width:16px; height:16px;">
              <div style="display:flex; flex-direction:column;">
                <span class="text-sm font-semibold text-main">Permitir criar e gerenciar usuários</span>
              </div>
            </label>
            <div id="limiteCriacaoContainer" style="margin-top: 0.5rem; display: none;">
              <label class="form-label" style="font-size: 0.8rem;">Limite de criação de usuários (deixe vazio para sem limite)</label>
              <input type="number" id="formUserLimiteCriacao" class="form-control" style="max-width: 150px; padding: 0.25rem 0.5rem; min-height: 30px;">
            </div>
            <label id="podeSimularContainer" style="display:none; align-items:center; gap:0.5rem; cursor:pointer; margin-top: 0.75rem; border-top: 1px solid var(--border-color); padding-top: 0.75rem;">
              <input type="checkbox" id="formUserPodeSimular" style="width:16px; height:16px;">
              <div style="display:flex; flex-direction:column;">
                <span class="text-sm font-semibold text-main">Permitir Simular Visões (Acessos)</span>
                <small class="text-xs text-muted" style="font-weight: normal;">Pode ver os dados como se fosse outro perfil.</small>
              </div>
            </label>
          </div>'''
# Some encoding issues with characters in index.html for select string... let's just find id="formUserPodeCriar"
# We will use simple replace
import re
idx_content = re.sub(
    r'<div id="podeCriarContainer".*?</label>\s*</div>',
    idx_pode_criar_new,
    idx_content,
    flags=re.DOTALL
)
with open(path_index, 'w', encoding='utf-8') as f:
    f.write(idx_content)

print('Backend and HTML updated.')
