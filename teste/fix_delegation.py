path = r'C:\Users\karen.xavier\Desktop\pluraal saas\Backend\services\delegation_service.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# I need to add validation for pode_simular_visao and Administrador to validate_delegation!
import re

old_def = 'def validate_delegation(creator_user_id: int, target_hierarquia: str, accesses_to_grant: list, target_pode_criar_usuario: bool, is_edit: bool, cur, target_user_id: int = None):'
new_def = 'def validate_delegation(creator_user_id: int, target_hierarquia: str, accesses_to_grant: list, target_pode_criar_usuario: bool, is_edit: bool, cur, target_user_id: int = None, target_pode_simular_visao: bool = False):'
text = text.replace(old_def, new_def)

# Find "if target_pode_criar_usuario and not is_creator_master:"
# and insert target_pode_simular_visao check
old_check = '''    if target_pode_criar_usuario and not is_creator_master:
        return False, "Somente o Master pode conceder a permissǜo de criar usuǭrios (pode_criar_usuario)."'''
new_check = '''    if target_pode_criar_usuario and not is_creator_master:
        return False, "Somente o Master pode conceder a permissǜo de criar usuǭrios (pode_criar_usuario)."
    if target_pode_simular_visao and not is_creator_master:
        return False, "Apenas o Master pode conceder a permissǜo de simular vises."
    if target_hierarquia == "Administrador" and not is_creator_master:
        return False, "Apenas o Master pode criar usuǭrios do tipo Administrador."'''
text = text.replace(old_check, new_check)

# Find "valid_target_hierarchies" dict
old_hier = '''    valid_target_hierarchies = {
        "Master": ["Master", "uniao", "associacao", "escola"],
        "uniao": ["uniao", "associacao", "escola"],
        "associacao": ["associacao", "escola"],
        "escola": ["escola"]
    }'''
new_hier = '''    valid_target_hierarchies = {
        "Master": ["Master", "Administrador", "uniao", "associacao", "escola"],
        "Administrador": ["Administrador", "uniao", "associacao", "escola"],
        "uniao": ["uniao", "associacao", "escola"],
        "associacao": ["associacao", "escola"],
        "escola": ["escola"]
    }'''
text = text.replace(old_hier, new_hier)

# In user_service.py, validate_delegation calls must include target_pode_simular_visao
with open(r'C:\Users\karen.xavier\Desktop\pluraal saas\Backend\services\user_service.py', 'r', encoding='utf-8') as f:
    usr_text = f.read()

usr_old1 = '''        valid, error_msg = validate_delegation(
            creator_user_id=creator_id,
            target_hierarquia=hierarquia,
            accesses_to_grant=acessos,
            target_pode_criar_usuario=pode_criar_usuario,
            is_edit=False,
            cur=cur
        )'''
usr_new1 = '''        valid, error_msg = validate_delegation(
            creator_user_id=creator_id,
            target_hierarquia=hierarquia,
            accesses_to_grant=acessos,
            target_pode_criar_usuario=pode_criar_usuario,
            is_edit=False,
            cur=cur,
            target_pode_simular_visao=pode_simular_visao
        )'''
usr_text = usr_text.replace(usr_old1, usr_new1)

usr_old2 = '''        valid, error_msg = validate_delegation(
            creator_user_id=updater_id,
            target_hierarquia=hierarquia,
            accesses_to_grant=acessos,
            target_pode_criar_usuario=pode_criar_usuario,
            is_edit=True,
            target_user_id=target_id,
            cur=cur
        )'''
usr_new2 = '''        valid, error_msg = validate_delegation(
            creator_user_id=updater_id,
            target_hierarquia=hierarquia,
            accesses_to_grant=acessos,
            target_pode_criar_usuario=pode_criar_usuario,
            is_edit=True,
            target_user_id=target_id,
            cur=cur,
            target_pode_simular_visao=pode_simular_visao
        )'''
usr_text = usr_text.replace(usr_old2, usr_new2)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

with open(r'C:\Users\karen.xavier\Desktop\pluraal saas\Backend\services\user_service.py', 'w', encoding='utf-8') as f:
    f.write(usr_text)

print('Delegation service updated.')
