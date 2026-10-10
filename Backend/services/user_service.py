from datetime import date
from Backend.database.connection import get_db_cursor
from Backend.services.security_service import (
    hash_password,
    generate_temporary_password
)
from Backend.services.delegation_service import (
    validate_delegation,
    check_reduction_impact_on_subordinates,
    get_effective_user_scope
)

def get_user_by_email(email: str):
    with get_db_cursor(commit=False) as cur:
        cur.execute("""
            SELECT id_usuario, nome_completo_usuario, email, senha, hierarquia,
                   ativo, trocar_senha_no_primeiro_acesso, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios,
                   criado_por_usuario_id, criado_em, token_versao, foto_perfil, paginas_permitidas, pode_cadastrar_escola,
                   data_expiracao_login,
                   (data_expiracao_login IS NOT NULL AND data_expiracao_login < CURRENT_DATE) AS login_expirado
            FROM pluraal.usuario
            WHERE LOWER(email) = LOWER(%s)
        """, (email.strip(),))
        return cur.fetchone()

def get_user_by_id(user_id: int):
    with get_db_cursor(commit=False) as cur:
        cur.execute("""
            SELECT id_usuario, nome_completo_usuario, email, hierarquia,
                   ativo, trocar_senha_no_primeiro_acesso, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios,
                   criado_por_usuario_id, criado_em, token_versao, foto_perfil, paginas_permitidas, pode_cadastrar_escola,
                   data_expiracao_login
            FROM pluraal.usuario
            WHERE id_usuario = %s
        """, (user_id,))
        user = cur.fetchone()
        if not user:
            return None
        if user["data_expiracao_login"]:
            user["data_expiracao_login"] = user["data_expiracao_login"].isoformat()
        
        # Load user accesses
        cur.execute("""
            SELECT ua.id_acesso, ua.tipo, ua.sigla_uniao, ua.sigla_associacao, ua.id_escolas,
                   ep."ESCOLA" as nome_escola, ep."UNIAO" as nome_uniao, ep."ASSOCIACAO" as nome_associacao
            FROM pluraal.usuario_acesso ua
            LEFT JOIN pluraal.escolas_pluraal ep ON ua.id_escolas = ep.id_escolas
            WHERE ua.id_usuario = %s
            ORDER BY ua.tipo, ua.sigla_uniao, ua.sigla_associacao
        """, (user_id,))
        user["acessos"] = cur.fetchall()

        return user


def _parse_expiration(value):
    if value in (None, ""):
        return None
    try:
        parsed = date.fromisoformat(value) if isinstance(value, str) else value
    except (TypeError, ValueError):
        raise ValueError("Data de expiração inválida. Use o formato AAAA-MM-DD.")
    if not isinstance(parsed, date) or parsed < date.today():
        raise ValueError("A data de expiração deve ser hoje ou uma data futura.")
    return parsed


def _parse_user_limit(value):
    if value in (None, ""):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError("O limite de criação de usuários deve ser um número inteiro.")
    if number < 0:
        raise ValueError("O limite de criação de usuários não pode ser negativo.")
    return number

def list_users(requester_id: int):
    with get_db_cursor(commit=False) as cur:
        cur.execute("""
            SELECT id_usuario, hierarquia, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios, paginas_permitidas, pode_cadastrar_escola
            FROM pluraal.usuario
            WHERE id_usuario = %s
        """, (requester_id,))
        requester = cur.fetchone()
        if not requester:
            raise ValueError("Usuário solicitante não encontrado.")
        if requester["hierarquia"] != "Master" and not requester["pode_criar_usuario"]:
            raise PermissionError("Você não tem permissão para gerenciar usuários.")

        if requester["hierarquia"] == "Master":
            cur.execute("""
                SELECT u.id_usuario, u.nome_completo_usuario, u.email, u.hierarquia,
                       u.ativo, u.trocar_senha_no_primeiro_acesso, u.pode_criar_usuario, u.pode_simular_visao, u.limite_criacao_usuarios, u.pode_cadastrar_escola,
                       u.criado_por_usuario_id, u.criado_em, u.data_expiracao_login,
                       creator.nome_completo_usuario as criado_por_nome
                FROM pluraal.usuario u
                LEFT JOIN pluraal.usuario creator ON u.criado_por_usuario_id = creator.id_usuario
                ORDER BY u.id_usuario ASC
            """)
            users = cur.fetchall()
        else:
            # Gestores veem somente os usuários que criaram diretamente.
            cur.execute("""
                SELECT u.id_usuario, u.nome_completo_usuario, u.email, u.hierarquia,
                       u.ativo, u.trocar_senha_no_primeiro_acesso, u.pode_criar_usuario, u.pode_simular_visao, u.limite_criacao_usuarios, u.pode_cadastrar_escola,
                       u.criado_por_usuario_id, u.criado_em, u.data_expiracao_login,
                       creator.nome_completo_usuario as criado_por_nome
                FROM pluraal.usuario u
                LEFT JOIN pluraal.usuario creator ON u.criado_por_usuario_id = creator.id_usuario
                WHERE u.criado_por_usuario_id = %s
                ORDER BY u.id_usuario ASC
            """, (requester_id,))
            users = cur.fetchall()
            hierarchy_rank = {"Master": 0, "Administrador": 1, "uniao": 2, "associacao": 3, "escola": 4}
            users = [u for u in users if hierarchy_rank.get(u["hierarquia"], -1) >= hierarchy_rank.get(requester["hierarquia"], 99)]

        # Attach summarized accesses
        for u in users:
            if u["data_expiracao_login"]:
                u["data_expiracao_login"] = u["data_expiracao_login"].isoformat()
            cur.execute("""
                SELECT ua.tipo, ua.sigla_uniao, ua.sigla_associacao, ua.id_escolas,
                       ep."ESCOLA" as nome_escola
                FROM pluraal.usuario_acesso ua
                LEFT JOIN pluraal.escolas_pluraal ep ON ua.id_escolas = ep.id_escolas
                WHERE ua.id_usuario = %s
            """, (u["id_usuario"],))
            u["acessos"] = cur.fetchall()

        return users

def create_user(creator_id: int, user_data: dict):
    nome = (user_data.get("nome_completo_usuario") or "").strip()
    email = (user_data.get("email") or "").strip().lower()
    hierarquia = user_data.get("hierarquia")
    ativo = user_data.get("ativo", True)
    pode_criar_usuario = user_data.get("pode_criar_usuario", False)
    pode_simular_visao = user_data.get("pode_simular_visao", False)
    limite_criacao_usuarios = _parse_user_limit(user_data.get("limite_criacao_usuarios"))
    acessos = user_data.get("acessos", [])
    paginas_permitidas = user_data.get("paginas_permitidas", [])
    data_expiracao_login = _parse_expiration(user_data.get("data_expiracao_login"))

    if not nome:
        raise ValueError("O nome completo do usuário é obrigatório.")
    if not email or "@" not in email:
        raise ValueError("E-mail inválido.")
    if not hierarquia:
        raise ValueError("A hierarquia do usuário é obrigatória.")

    with get_db_cursor(commit=True) as cur:
        # Check creator's pages
        cur.execute("SELECT hierarquia, paginas_permitidas FROM pluraal.usuario WHERE id_usuario = %s", (creator_id,))
        creator = cur.fetchone()
        if not creator:
            raise PermissionError("Criador não encontrado.")
        
        creator_pages = creator.get("paginas_permitidas") or []
        if creator["hierarquia"] != "Master":
            for p in paginas_permitidas:
                if p not in creator_pages:
                    raise PermissionError(f"Você não tem permissão para conceder acesso à página '{p}'.")

        # Check email uniqueness
        cur.execute("SELECT id_usuario FROM pluraal.usuario WHERE LOWER(email) = LOWER(%s)", (email,))
        if cur.fetchone():
            raise ValueError(f"O e-mail '{email}' já está em uso por outro usuário.")

        # Validate delegation rules
        is_valid, err_msg = validate_delegation(
            creator_user_id=creator_id,
            target_hierarquia=hierarquia,
            accesses_to_grant=acessos,
            target_pode_criar_usuario=pode_criar_usuario,
            target_pode_simular_visao=pode_simular_visao,
            is_edit=False,
            cur=cur
        )
        if not is_valid:
            raise PermissionError(err_msg)

        # Check limit
        cur.execute("SELECT limite_criacao_usuarios FROM pluraal.usuario WHERE id_usuario = %s", (creator_id,))
        creator_limit_row = cur.fetchone()
        if creator_limit_row and creator_limit_row.get("limite_criacao_usuarios") is not None:
            cur.execute("SELECT COUNT(*) as total FROM pluraal.usuario WHERE criado_por_usuario_id = %s", (creator_id,))
            created_count = cur.fetchone()["total"]
            if created_count >= creator_limit_row["limite_criacao_usuarios"]:
                raise PermissionError("Você atingiu o limite máximo de usuários que pode criar.")

        # Generate temporary password
        temp_password = generate_temporary_password(10)
        password_hash = hash_password(temp_password)

        # Insert user
        cur.execute("""
            INSERT INTO pluraal.usuario (
                nome_completo_usuario, email, senha, hierarquia,
                ativo, trocar_senha_no_primeiro_acesso, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios,
                criado_por_usuario_id, criado_em, token_versao, paginas_permitidas, pode_cadastrar_escola,
                data_expiracao_login
            ) VALUES (
                %s, %s, %s, %s,
                %s, true, %s, %s, %s,
                %s, now(), 1, %s, %s, %s
            ) RETURNING id_usuario, criado_em;
        """, (nome, email, password_hash, hierarquia, ativo, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios, creator_id, paginas_permitidas, user_data.get("pode_cadastrar_escola", False), data_expiracao_login))
        res = cur.fetchone()
        new_user_id = res["id_usuario"]

        # Insert accesses if not Master
        if hierarquia != "Master" and acessos:
            for acc in acessos:
                cur.execute("""
                    INSERT INTO pluraal.usuario_acesso (
                        id_usuario, tipo, sigla_uniao, sigla_associacao, id_escolas
                    ) VALUES (%s, %s, %s, %s, %s);
                """, (
                    new_user_id,
                    acc.get("tipo"),
                    acc.get("sigla_uniao"),
                    acc.get("sigla_associacao"),
                    acc.get("id_escolas")
                ))

        return {
            "id_usuario": new_user_id,
            "nome_completo_usuario": nome,
            "email": email,
            "hierarquia": hierarquia,
            "ativo": ativo,
            "pode_criar_usuario": pode_criar_usuario,
            "pode_simular_visao": pode_simular_visao,
            "limite_criacao_usuarios": limite_criacao_usuarios,
            "data_expiracao_login": data_expiracao_login.isoformat() if data_expiracao_login else None,
            "senha_temporaria": temp_password  # Displayed ONLY ONCE
        }

def update_user(updater_id: int, target_id: int, update_data: dict):
    nome = (update_data.get("nome_completo_usuario") or "").strip()
    email = (update_data.get("email") or "").strip().lower()
    hierarquia = update_data.get("hierarquia")
    ativo = update_data.get("ativo", True)
    pode_criar_usuario = update_data.get("pode_criar_usuario", False)
    pode_simular_visao = update_data.get("pode_simular_visao", False)
    limite_criacao_usuarios = _parse_user_limit(update_data.get("limite_criacao_usuarios"))
    acessos = update_data.get("acessos", [])
    paginas_permitidas = update_data.get("paginas_permitidas", [])
    pode_cadastrar_escola = update_data.get("pode_cadastrar_escola")
    data_expiracao_login = _parse_expiration(update_data.get("data_expiracao_login"))

    if not nome:
        raise ValueError("O nome completo do usuário é obrigatório.")
    if not email or "@" not in email:
        raise ValueError("E-mail inválido.")

    with get_db_cursor(commit=True) as cur:
        # Check target user exists
        cur.execute("""
            SELECT id_usuario, hierarquia, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios, pode_cadastrar_escola,
                   criado_por_usuario_id, ativo, token_versao,
                   data_expiracao_login
            FROM pluraal.usuario
            WHERE id_usuario = %s
        """, (target_id,))
        target_user = cur.fetchone()
        if not target_user:
            raise ValueError(f"Usuário {target_id} não encontrado.")
        if pode_cadastrar_escola is None:
            pode_cadastrar_escola = target_user["pode_cadastrar_escola"]

        # Check updater
        cur.execute("""
            SELECT id_usuario, hierarquia, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios, paginas_permitidas
            FROM pluraal.usuario
            WHERE id_usuario = %s
        """, (updater_id,))
        updater = cur.fetchone()
        if not updater:
            raise ValueError("Usuário solicitante não encontrado.")

        is_master = (updater["hierarquia"] == "Master")
        if not is_master and (not updater["pode_criar_usuario"] or target_user["criado_por_usuario_id"] != updater_id):
            raise PermissionError("Você só pode editar usuários que criou diretamente.")
        hierarchy_rank = {"Master": 0, "Administrador": 1, "uniao": 2, "associacao": 3, "escola": 4}
        if not is_master and hierarchy_rank.get(target_user["hierarquia"], -1) < hierarchy_rank.get(updater["hierarquia"], 99):
            raise PermissionError("Você não pode editar usuários de hierarquia superior à sua.")
        if not is_master:
            pode_cadastrar_escola = target_user["pode_cadastrar_escola"]
        if not is_master and limite_criacao_usuarios != target_user["limite_criacao_usuarios"]:
            raise PermissionError("Apenas o Master pode alterar o limite de criação de usuários.")
        updater_pages = updater.get("paginas_permitidas") or []
        
        if not is_master:
            for p in paginas_permitidas:
                if p not in updater_pages:
                    raise PermissionError(f"Você não tem permissão para conceder acesso à página '{p}'.")

        # Non-master cannot edit self hierarchy/accesses
        if updater_id == target_id and not is_master:
            raise PermissionError("Usuários não-master não podem editar seu próprio perfil.")

        # Check unique email
        cur.execute("SELECT id_usuario FROM pluraal.usuario WHERE LOWER(email) = LOWER(%s) AND id_usuario != %s", (email, target_id))
        if cur.fetchone():
            raise ValueError(f"O e-mail '{email}' já está em uso por outro usuário.")

        # Validate delegation bounds
        is_valid, err_msg = validate_delegation(
            creator_user_id=updater_id,
            target_hierarquia=hierarquia,
            accesses_to_grant=acessos,
            target_pode_criar_usuario=pode_criar_usuario,
            target_pode_simular_visao=pode_simular_visao,
            is_edit=True,
            target_user_id=target_id,
            cur=cur
        )
        if not is_valid:
            raise PermissionError(err_msg)

        # Check if reduction impacts existing subordinates created by target_id
        if target_user["hierarquia"] != "Master" or hierarquia != "Master":
            can_reduce, red_msg, conflicts = check_reduction_impact_on_subordinates(
                creator_user_id=target_id,
                new_hierarquia=hierarquia,
                new_access_list=acessos,
                cur=cur
            )
            if not can_reduce:
                err = {
                    "error": "DELEGATION_REDUCTION_CONFLICT",
                    "message": red_msg,
                    "conflitos": conflicts
                }
                raise ValueError(err)

        # If user deactivated, increment token_versao to invalidate sessions
        new_token_versao = target_user["token_versao"]
        if (not ativo and target_user["ativo"]) or data_expiracao_login != target_user["data_expiracao_login"]:
            new_token_versao += 1

        # Update usuario record
        cur.execute("""
            UPDATE pluraal.usuario
            SET nome_completo_usuario = %s,
                email = %s,
                hierarquia = %s,
                ativo = %s,
                pode_criar_usuario = %s,
                pode_simular_visao = %s,
                limite_criacao_usuarios = %s,
                token_versao = %s,
                paginas_permitidas = %s,
                pode_cadastrar_escola = %s,
                data_expiracao_login = %s
            WHERE id_usuario = %s;
        """, (nome, email, hierarquia, ativo, pode_criar_usuario, pode_simular_visao, limite_criacao_usuarios, new_token_versao, paginas_permitidas, pode_cadastrar_escola, data_expiracao_login, target_id))

        # Replace accesses
        cur.execute("DELETE FROM pluraal.usuario_acesso WHERE id_usuario = %s", (target_id,))
        if hierarquia != "Master" and acessos:
            for acc in acessos:
                cur.execute("""
                    INSERT INTO pluraal.usuario_acesso (
                        id_usuario, tipo, sigla_uniao, sigla_associacao, id_escolas
                    ) VALUES (%s, %s, %s, %s, %s);
                """, (
                    target_id,
                    acc.get("tipo"),
                    acc.get("sigla_uniao"),
                    acc.get("sigla_associacao"),
                    acc.get("id_escolas")
                ))

        return {
            "id_usuario": target_id,
            "nome_completo_usuario": nome,
            "email": email,
            "hierarquia": hierarquia,
            "ativo": ativo,
            "pode_criar_usuario": pode_criar_usuario,
            "data_expiracao_login": data_expiracao_login.isoformat() if data_expiracao_login else None
        }

def reset_user_password(requester_id: int, target_id: int):
    """
    Authorized user resets target's password.
    Generates new temporary password, forces password change on next login,
    and invalidates existing sessions.
    Returns: temporary password (shown ONLY ONCE).
    """
    with get_db_cursor(commit=True) as cur:
        # Check requester permissions
        cur.execute("SELECT id_usuario, hierarquia, pode_criar_usuario FROM pluraal.usuario WHERE id_usuario = %s", (requester_id,))
        requester = cur.fetchone()
        if not requester:
            raise PermissionError("Usuário solicitante não encontrado.")

        cur.execute("SELECT id_usuario, hierarquia, criado_por_usuario_id, ativo FROM pluraal.usuario WHERE id_usuario = %s", (target_id,))
        target = cur.fetchone()
        if not target:
            raise ValueError("Usuário alvo não encontrado.")

        is_master = (requester["hierarquia"] == "Master")
        is_creator = (target["criado_por_usuario_id"] == requester_id)

        if not is_master and (not requester["pode_criar_usuario"] or not is_creator):
            raise PermissionError("Você não tem autorização para redefinir a senha deste usuário.")

        hierarchy_rank = {"Master": 0, "Administrador": 1, "uniao": 2, "associacao": 3, "escola": 4}
        if not is_master and hierarchy_rank.get(target["hierarquia"], -1) < hierarchy_rank.get(requester["hierarquia"], 99):
            raise PermissionError("Você não pode gerenciar usuários de hierarquia superior à sua.")

        if target["hierarquia"] == "Master" and not is_master:
            raise PermissionError("Apenas usuários Master podem redefinir a senha de outro Master.")

        # Generate temporary password
        temp_password = generate_temporary_password(10)
        pw_hash = hash_password(temp_password)

        # Update user: new password hash, force change on next login, invalidate all current sessions
        cur.execute("""
            UPDATE pluraal.usuario
            SET senha = %s,
                trocar_senha_no_primeiro_acesso = true,
                token_versao = token_versao + 1
            WHERE id_usuario = %s;
        """, (pw_hash, target_id))

        return {
            "id_usuario": target_id,
            "senha_temporaria": temp_password  # Displayed ONLY ONCE
        }

def update_user_photo(user_id: int, photo_base64: str):
    with get_db_cursor(commit=True) as cur:
        cur.execute("""
            UPDATE pluraal.usuario
            SET foto_perfil = %s
            WHERE id_usuario = %s;
        """, (photo_base64, user_id))
        
        cur.execute("SELECT foto_perfil FROM pluraal.usuario WHERE id_usuario = %s", (user_id,))
        return cur.fetchone()
