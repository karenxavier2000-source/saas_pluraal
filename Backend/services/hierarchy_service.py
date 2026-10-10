from Backend.database.connection import get_db_cursor
from Backend.services.delegation_service import get_effective_user_scope, get_all_escolas_catalog

def get_delegation_capabilities(user_id: int):
    """
    Returns what hierarchies the user can grant, whether they can grant pode_criar_usuario,
    and their allowed unioes, associacoes, and escolas.
    """
    with get_db_cursor(commit=False) as cur:
        scope = get_effective_user_scope(user_id, cur)
        catalog = get_all_escolas_catalog(cur)
        h = scope["hierarquia"]

        allowed_hierarchies = {
            "Master": ["Master", "Administrador", "uniao", "associacao", "escola"],
            "Administrador": ["Administrador", "uniao", "associacao", "escola"],
            "uniao": ["uniao", "associacao", "escola"],
            "associacao": ["associacao", "escola"],
            "escola": ["escola"]
        }.get(h, [])

        can_manage_pode_criar = (h == "Master")

        # Build clean lists of allowed unioes, associacoes, escolas
        # 1. Unioes
        unioes_list = []
        for u in sorted(scope["unioes"]):
            # Find name
            nome_u = u
            for info in catalog["escola_map"].values():
                if info["sigla_uniao"] == u and info["uniao"]:
                    nome_u = info["uniao"]
                    break
            unioes_list.append({"sigla_uniao": u, "nome_uniao": nome_u})

        # 2. Associacoes
        associacoes_list = []
        for (u, a) in sorted(scope["associacoes"]):
            nome_a = a
            for info in catalog["escola_map"].values():
                if info["sigla_uniao"] == u and info["sigla_associacao"] == a and info["associacao"]:
                    nome_a = info["associacao"]
                    break
            associacoes_list.append({"sigla_uniao": u, "sigla_associacao": a, "nome_associacao": nome_a})

        # 3. Escolas
        escolas_list = []
        for eid in sorted(scope["escolas"]):
            if eid in catalog["escola_map"]:
                info = catalog["escola_map"][eid]
                escolas_list.append({
                    "id_escolas": eid,
                    "escola": info["escola"],
                    "sigla_uniao": info["sigla_uniao"],
                    "sigla_associacao": info["sigla_associacao"]
                })

        return {
            "usuario_hierarquia": h,
            "pode_criar_usuario": scope["pode_criar_usuario"],
            "paginas_permitidas": scope.get("paginas_permitidas", []),
            "can_grant_pode_criar_usuario": can_manage_pode_criar,
            "can_grant_pode_simular": (h == "Master"),
            "allowed_target_hierarchies": allowed_hierarchies,
            "unioes": unioes_list,
            "associacoes": associacoes_list,
            "escolas": escolas_list
        }
