from Backend.database.connection import get_db_cursor

def get_all_escolas_catalog(cur):
    """
    Returns full catalog from escolas_pluraal:
    - all_unioes: set of SIGLA_UNIAO
    - all_associacoes: set of (SIGLA_UNIAO, SIGLA_ASSOCIACAO)
    - all_escolas: set of id_escolas
    - escola_map: dict id_escolas -> {id_escolas, ESCOLA, SIGLA_UNIAO, SIGLA_ASSOCIACAO, UNIAO, ASSOCIACAO}
    """
    cur.execute("""
        SELECT id_escolas, "UNIAO", "SIGLA_UNIAO", "ASSOCIACAO", "SIGLA_ASSOCIACAO", "ESCOLA"
        FROM pluraal.escolas_pluraal
        WHERE "SIGLA_UNIAO" IS NOT NULL AND "SIGLA_UNIAO" != 'SIGLA_UNIAO'
    """)
    rows = cur.fetchall()
    
    all_unioes = set()
    all_associacoes = set()
    all_escolas = set()
    escola_map = {}
    
    for r in rows:
        eid = r["id_escolas"]
        u = (r["SIGLA_UNIAO"] or "").strip()
        a = (r["SIGLA_ASSOCIACAO"] or "").strip()
        if u:
            all_unioes.add(u)
        if u and a:
            all_associacoes.add((u, a))
        if eid:
            all_escolas.add(eid)
            escola_map[eid] = {
                "id_escolas": eid,
                "escola": r["ESCOLA"],
                "sigla_uniao": u,
                "uniao": r["UNIAO"],
                "sigla_associacao": a,
                "associacao": r["ASSOCIACAO"]
            }
            
    return {
        "unioes": all_unioes,
        "associacoes": all_associacoes,
        "escolas": all_escolas,
        "escola_map": escola_map
    }

_HIERARCHY_ORDER = {"Master": 0, "Administrador": 1, "uniao": 2, "associacao": 3, "escola": 4}


def _apply_simulation(scope, user, catalog):
    from flask import request, has_request_context
    if not has_request_context():
        return scope
    level = request.headers.get("X-Simulate-Nivel")
    if not level:
        return scope
    if not (user["hierarquia"] == "Master" or user.get("pode_simular_visao")):
        raise PermissionError("Este usuário não tem permissão para simular visões.")
    if level not in _HIERARCHY_ORDER or _HIERARCHY_ORDER[level] <= _HIERARCHY_ORDER.get(user["hierarquia"], 99):
        raise PermissionError("A simulação deve usar um nível abaixo da hierarquia do usuário.")
    if level == "Administrador":
        result = dict(scope)
        result.update(hierarquia=level, is_simulated=True, pode_criar_usuario=False)
        return result

    union = request.headers.get("X-Simulate-Uniao", "").strip()
    assoc = request.headers.get("X-Simulate-Associacao", "").strip()
    school_raw = request.headers.get("X-Simulate-Escola", "").strip()
    if level not in ("uniao", "associacao", "escola"):
        raise PermissionError("Nível de simulação inválido.")
    if not union or (level in ("associacao", "escola") and not assoc) or (level == "escola" and not school_raw.isdigit()):
        raise ValueError("Selecione uma instituição válida para a simulação.")
    selected = {eid for eid, info in catalog["escola_map"].items()
                if info["sigla_uniao"] == union
                and (level == "uniao" or info["sigla_associacao"] == assoc)
                and (level != "escola" or eid == int(school_raw))}
    if not selected or not selected.issubset(scope["escolas"]):
        raise PermissionError("A instituição simulada está fora do seu escopo de acesso.")
    result = dict(scope)
    result.update(hierarquia=level, escolas=selected, is_simulated=True,
                  unioes={union},
                  associacoes={(u, a) for (u, a) in catalog["associacoes"] if u == union and
                               (level == "uniao" or a == assoc)},
                  pode_criar_usuario=False)
    return result


def get_effective_user_scope(id_usuario: int, cur, allow_simulation: bool = False):
    """
    Computes effective access for a user:
    Returns dict:
    {
        "hierarquia": str,
        "pode_criar_usuario": bool,
        "unioes": set of SIGLA_UNIAO,
        "associacoes": set of (SIGLA_UNIAO, SIGLA_ASSOCIACAO),
        "escolas": set of id_escolas (int)
    }
    """
    cur.execute("""
        SELECT id_usuario, hierarquia, pode_criar_usuario, pode_simular_visao, ativo, paginas_permitidas
        FROM pluraal.usuario
        WHERE id_usuario = %s
    """, (id_usuario,))
    user = cur.fetchone()
    if not user:
        raise ValueError(f"Usuário {id_usuario} não encontrado.")
    
    catalog = get_all_escolas_catalog(cur)
    hierarquia = user["hierarquia"]
    
    if hierarquia in ("Master", "Administrador"):
        base_scope = {
            "hierarquia": hierarquia,
            "pode_criar_usuario": user["pode_criar_usuario"],
            "pode_simular_visao": user["pode_simular_visao"],
            "paginas_permitidas": user.get("paginas_permitidas") or [],
            "unioes": catalog["unioes"],
            "associacoes": catalog["associacoes"],
            "escolas": catalog["escolas"]
        }
        return _apply_simulation(base_scope, user, catalog) if allow_simulation else base_scope

    # Query direct accesses assigned to the user
    cur.execute("""
        SELECT tipo, sigla_uniao, sigla_associacao, id_escolas
        FROM pluraal.usuario_acesso
        WHERE id_usuario = %s
    """, (id_usuario,))
    access_rows = cur.fetchall()
    
    effective_unioes = set()
    effective_associacoes = set()
    effective_escolas = set()
    
    for acc in access_rows:
        tipo = acc["tipo"]
        u = (acc["sigla_uniao"] or "").strip()
        a = (acc["sigla_associacao"] or "").strip()
        eid = acc["id_escolas"]
        
        if tipo == "uniao" and u:
            effective_unioes.add(u)
            # All associacoes and escolas in this uniao
            for (su, sa) in catalog["associacoes"]:
                if su == u:
                    effective_associacoes.add((su, sa))
            for eid_cat, info in catalog["escola_map"].items():
                if info["sigla_uniao"] == u:
                    effective_escolas.add(eid_cat)
                    
        elif tipo == "associacao" and u and a:
            effective_unioes.add(u)
            effective_associacoes.add((u, a))
            # All escolas in this associacao
            for eid_cat, info in catalog["escola_map"].items():
                if info["sigla_uniao"] == u and info["sigla_associacao"] == a:
                    effective_escolas.add(eid_cat)
                    
        elif tipo == "escola" and eid:
            effective_escolas.add(eid)
            if eid in catalog["escola_map"]:
                info = catalog["escola_map"][eid]
                effective_unioes.add(info["sigla_uniao"])
                effective_associacoes.add((info["sigla_uniao"], info["sigla_associacao"]))

    base_scope = {
        "hierarquia": hierarquia,
        "pode_criar_usuario": user["pode_criar_usuario"],
        "pode_simular_visao": user["pode_simular_visao"],
        "paginas_permitidas": user.get("paginas_permitidas") or [],
        "unioes": effective_unioes,
        "associacoes": effective_associacoes,
        "escolas": effective_escolas
    }
    return _apply_simulation(base_scope, user, catalog) if allow_simulation else base_scope

def compute_effective_scope_from_access_list(hierarquia: str, access_list: list, cur):
    """
    Computes effective scope given a proposed hierarchy and access list.
    access_list is a list of dicts: [{'tipo': '...', 'sigla_uniao': '...', 'sigla_associacao': '...', 'id_escolas': ...}]
    """
    catalog = get_all_escolas_catalog(cur)
    if hierarquia in ("Master", "Administrador"):
        return {
            "hierarquia": "Master",
            "unioes": catalog["unioes"],
            "associacoes": catalog["associacoes"],
            "escolas": catalog["escolas"]
        }
        
    effective_unioes = set()
    effective_associacoes = set()
    effective_escolas = set()
    
    for acc in access_list:
        tipo = acc.get("tipo")
        u = (acc.get("sigla_uniao") or "").strip()
        a = (acc.get("sigla_associacao") or "").strip()
        eid = acc.get("id_escolas")
        
        if tipo == "uniao" and u:
            effective_unioes.add(u)
            for (su, sa) in catalog["associacoes"]:
                if su == u:
                    effective_associacoes.add((su, sa))
            for eid_cat, info in catalog["escola_map"].items():
                if info["sigla_uniao"] == u:
                    effective_escolas.add(eid_cat)
                    
        elif tipo == "associacao" and u and a:
            effective_unioes.add(u)
            effective_associacoes.add((u, a))
            for eid_cat, info in catalog["escola_map"].items():
                if info["sigla_uniao"] == u and info["sigla_associacao"] == a:
                    effective_escolas.add(eid_cat)
                    
        elif tipo == "escola" and eid:
            effective_escolas.add(eid)
            if eid in catalog["escola_map"]:
                info = catalog["escola_map"][eid]
                effective_unioes.add(info["sigla_uniao"])
                effective_associacoes.add((info["sigla_uniao"], info["sigla_associacao"]))
                
    return {
        "hierarquia": hierarquia,
        "unioes": effective_unioes,
        "associacoes": effective_associacoes,
        "escolas": effective_escolas
    }

def validate_delegation(creator_user_id: int, target_hierarquia: str, accesses_to_grant: list, target_pode_criar_usuario: bool, target_pode_simular_visao: bool = False, target_pode_cadastrar_escola: bool = False, is_edit: bool = False, target_user_id: int = None, cur = None):
    """
    Validates all delegation rules:
    - Master can create anything and grant pode_criar_usuario.
    - Non-master must have pode_criar_usuario = True.
    - Non-master cannot create Master.
    - Non-master cannot grant pode_criar_usuario.
    - Non-master cannot edit their own hierarchy or accesses.
    - Hierarchy bounds:
        - uniao can create: uniao, associacao, escola (within their unions)
        - associacao can create: associacao, escola (within their associacoes)
        - escola can create: escola (within their escolas)
    - Effective access of created user cannot exceed creator's effective access.
    
    Returns: (is_valid: bool, error_message: str)
    """
    cur.execute("""
        SELECT id_usuario, hierarquia, pode_criar_usuario, ativo
        FROM pluraal.usuario
        WHERE id_usuario = %s
    """, (creator_user_id,))
    creator = cur.fetchone()
    if not creator or not creator["ativo"]:
        return False, "Usuário criador não encontrado ou inativo."

    is_creator_master = (creator["hierarquia"] == "Master")

    # 1. Non-master must have pode_criar_usuario
    if not is_creator_master and not creator["pode_criar_usuario"]:
        return False, "Você não possui permissão para criar ou gerenciar usuários (pode_criar_usuario = false)."

    # 2. Non-master cannot create or edit Master
    if target_hierarquia == "Master" and not is_creator_master:
        return False, "Apenas usuários Master podem criar ou gerenciar usuários com hierarquia Master."

    # 3. Apenas Master concede gestão de usuários e simulação.
    if not is_creator_master and (target_pode_criar_usuario or target_pode_simular_visao):
        existing = None
        if is_edit and target_user_id:
            cur.execute("SELECT pode_criar_usuario, pode_simular_visao FROM pluraal.usuario WHERE id_usuario = %s", (target_user_id,))
            existing = cur.fetchone()
        if target_pode_criar_usuario and not (existing and existing["pode_criar_usuario"]):
            return False, "Somente o Master pode conceder a permissão de criar usuários (pode_criar_usuario)."
        if target_pode_simular_visao and not (existing and existing["pode_simular_visao"]):
            return False, "Somente o Master pode conceder a permissão de simular visões."
    if not is_creator_master and is_edit and target_user_id:
        cur.execute("SELECT pode_criar_usuario, pode_simular_visao FROM pluraal.usuario WHERE id_usuario = %s", (target_user_id,))
        existing = cur.fetchone()
        if existing and (bool(existing["pode_criar_usuario"]) != bool(target_pode_criar_usuario)
                         or bool(existing["pode_simular_visao"]) != bool(target_pode_simular_visao)):
            return False, "Apenas o Master pode alterar permissões de gestão ou simulação."

    if is_edit and target_user_id and not is_creator_master:
        cur.execute("SELECT criado_por_usuario_id FROM pluraal.usuario WHERE id_usuario = %s", (target_user_id,))
        target = cur.fetchone()
        if not target or target["criado_por_usuario_id"] != creator_user_id:
            return False, "Você só pode gerenciar usuários que criou diretamente."

    # 4. Non-master cannot alter their own hierarchy or accesses
    if is_edit and target_user_id and target_user_id == creator_user_id and not is_creator_master:
        return False, "Um usuário não Master nunca pode alterar sua própria hierarquia ou seus próprios acessos."

    # 5. Hierarchy delegation rules
    creator_h = creator["hierarquia"]
    allowed_target_h = {
        "Master": ["Master", "Administrador", "uniao", "associacao", "escola"],
        "Administrador": ["Administrador", "uniao", "associacao", "escola"],
        "uniao": ["uniao", "associacao", "escola"],
        "associacao": ["associacao", "escola"],
        "escola": ["escola"]
    }

    if target_hierarquia not in allowed_target_h.get(creator_h, []):
        return False, f"Um usuário com hierarquia '{creator_h}' não pode criar ou definir usuários com hierarquia '{target_hierarquia}'."

    if target_hierarquia not in ("Master", "Administrador") and not accesses_to_grant:
        return False, "O usuário deve possuir pelo menos um acesso atribuído (União, Associação ou Escola)."

    # If creator is Master, full access is guaranteed
    if is_creator_master:
        return True, ""

    # 6. Check scope delegation bounds for non-master creator
    creator_scope = get_effective_user_scope(creator_user_id, cur)
    
    # Target cannot have empty accesses if not Master
    for acc in accesses_to_grant:
        tipo = acc.get("tipo")
        u = (acc.get("sigla_uniao") or "").strip()
        a = (acc.get("sigla_associacao") or "").strip()
        eid = acc.get("id_escolas")

        if tipo == "uniao":
            if creator_h not in ("Administrador", "uniao"):
                return False, f"Usuários com hierarquia '{creator_h}' não podem conceder acesso a nível de União."
            if u not in creator_scope["unioes"]:
                return False, f"Acesso à união '{u}' está fora do escopo do criador."

        elif tipo == "associacao":
            if creator_h not in ("Administrador", "uniao", "associacao"):
                return False, f"Usuários com hierarquia '{creator_h}' não podem conceder acesso a nível de Associação."
            if (u, a) not in creator_scope["associacoes"]:
                return False, f"Acesso à associação '{u} - {a}' está fora do escopo do criador."

        elif tipo == "escola":
            if not eid:
                return False, "ID da escola é obrigatório para acesso do tipo 'escola'."
            if eid not in creator_scope["escolas"]:
                return False, f"Acesso à escola ID {eid} está fora do escopo do criador."

    # Target effective schools must be a subset of creator effective schools
    target_scope = compute_effective_scope_from_access_list(target_hierarquia, accesses_to_grant, cur)
    if not target_scope["escolas"].issubset(creator_scope["escolas"]):
        excess = target_scope["escolas"] - creator_scope["escolas"]
        return False, f"O acesso efetivo do usuário criado ({len(target_scope['escolas'])} escolas) excede o acesso do criador. Escolas fora do limite: {list(excess)[:5]}"

    return True, ""

def check_reduction_impact_on_subordinates(creator_user_id: int, new_hierarquia: str, new_access_list: list, cur):
    """
    Checks if reducing creator's access violates any subordinate users' access.
    Returns: (can_update: bool, message: str, conflicts: list)
    """
    cur.execute("""
        SELECT id_usuario, nome_completo_usuario, hierarquia
        FROM pluraal.usuario
        WHERE criado_por_usuario_id = %s AND ativo = true
    """, (creator_user_id,))
    subordinates = cur.fetchall()

    if not subordinates:
        return True, "", []

    new_scope = compute_effective_scope_from_access_list(new_hierarquia, new_access_list, cur)
    catalog = get_all_escolas_catalog(cur)
    
    conflicts = []

    for sub in subordinates:
        sub_scope = get_effective_user_scope(sub["id_usuario"], cur)
        excess_escolas = sub_scope["escolas"] - new_scope["escolas"]
        
        if excess_escolas:
            detailed_excess = []
            for eid in excess_escolas:
                if eid in catalog["escola_map"]:
                    e_info = catalog["escola_map"][eid]
                    detailed_excess.append({
                        "id_escolas": eid,
                        "escola": e_info["escola"],
                        "uniao": e_info["sigla_uniao"],
                        "associacao": e_info["sigla_associacao"]
                    })
                else:
                    detailed_excess.append({"id_escolas": eid})

            conflicts.append({
                "id_usuario": sub["id_usuario"],
                "nome_completo_usuario": sub["nome_completo_usuario"],
                "hierarquia": sub["hierarquia"],
                "total_escolas_excedentes": len(excess_escolas),
                "escolas_excedentes": detailed_excess[:10]  # limit sample to 10 for clean presentation
            })

    if conflicts:
        msg = (
            "Não é possível reduzir os acessos deste criador pois existem usuários subordinados "
            "com acessos que ficariam fora do novo limite. Corrija primeiro os acessos dos subordinados listados."
        )
        return False, msg, conflicts

    return True, "", []
