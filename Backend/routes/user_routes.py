from flask import Blueprint, request, jsonify, g
from Backend.services.user_service import (
    list_users,
    get_user_by_id,
    create_user,
    update_user,
    reset_user_password,
    update_user_photo
)
from Backend.middleware.auth_middleware import login_required

user_bp = Blueprint("users", __name__, url_prefix="/api/users")

@user_bp.route("", methods=["GET"])
@login_required()
def get_users():
    try:
        users = list_users(g.current_user["id_usuario"])
        return jsonify(users), 200
    except PermissionError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403
    except Exception as e:
        return jsonify({"error": "SERVER_ERROR", "message": str(e)}), 500

@user_bp.route("/<int:user_id>", methods=["GET"])
@login_required()
def get_single_user(user_id):
    try:
        requester = g.current_user
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "NOT_FOUND", "message": "Usuário não encontrado."}), 404
        if (requester["hierarquia"] != "Master" and user_id != requester["id_usuario"]
                and (not requester["pode_criar_usuario"] or user["criado_por_usuario_id"] != requester["id_usuario"])):
            return jsonify({"error": "FORBIDDEN", "message": "Você só pode consultar usuários que criou diretamente."}), 403
        hierarchy_rank = {"Master": 0, "Administrador": 1, "uniao": 2, "associacao": 3, "escola": 4}
        if (requester["hierarquia"] != "Master" and user_id != requester["id_usuario"]
                and hierarchy_rank.get(user["hierarquia"], -1) < hierarchy_rank.get(requester["hierarquia"], 99)):
            return jsonify({"error": "FORBIDDEN", "message": "Você não pode consultar usuários de hierarquia superior à sua."}), 403
        return jsonify(user), 200
    except Exception as e:
        return jsonify({"error": "SERVER_ERROR", "message": str(e)}), 500

@user_bp.route("", methods=["POST"])
@login_required()
def handle_create_user():
    data = request.get_json(silent=True) or {}
    try:
        creator_id = g.current_user["id_usuario"]
        new_user = create_user(creator_id, data)
        return jsonify({
            "message": "Usuário cadastrado com sucesso!",
            "user": new_user
        }), 201
    except PermissionError as e:
        return jsonify({"error": "DELEGATION_ERROR", "message": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": "VALIDATION_ERROR", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "SERVER_ERROR", "message": "Erro ao criar usuário: " + str(e)}), 500

@user_bp.route("/<int:user_id>", methods=["PUT"])
@login_required()
def handle_update_user(user_id):
    data = request.get_json(silent=True) or {}
    try:
        updater_id = g.current_user["id_usuario"]
        updated_user = update_user(updater_id, user_id, data)
        return jsonify({
            "message": "Usuário atualizado com sucesso!",
            "user": updated_user
        }), 200
    except PermissionError as e:
        return jsonify({"error": "DELEGATION_ERROR", "message": str(e)}), 403
    except ValueError as e:
        # Check if structured reduction conflict
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        return jsonify({"error": "VALIDATION_ERROR", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "SERVER_ERROR", "message": "Erro ao atualizar usuário: " + str(e)}), 500

@user_bp.route("/<int:user_id>/reset-password", methods=["POST"])
@login_required()
def handle_reset_password(user_id):
    try:
        requester_id = g.current_user["id_usuario"]
        res = reset_user_password(requester_id, user_id)
        return jsonify({
            "message": "Senha temporária gerada com sucesso! As sessões ativas do usuário foram encerradas e a alteração de senha será obrigatória no próximo login.",
            **res
        }), 200
    except PermissionError as e:
        return jsonify({"error": "FORBIDDEN", "message": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"error": "SERVER_ERROR", "message": "Erro ao redefinir senha: " + str(e)}), 500

@user_bp.route("/<int:user_id>/photo", methods=["POST"])
@login_required()
def handle_update_photo(user_id):
    data = request.get_json(silent=True) or {}
    try:
        requester_id = g.current_user["id_usuario"]
        if requester_id != user_id:
            return jsonify({"error": "FORBIDDEN", "message": "Você só pode alterar a sua própria foto."}), 403
        
        photo_base64 = data.get("foto_perfil")
        if photo_base64 and len(photo_base64) > 10 * 1024 * 1024:
            return jsonify({"error": "PAYLOAD_TOO_LARGE", "message": "A imagem excede 10MB."}), 413
            
        updated = update_user_photo(user_id, photo_base64)
        return jsonify({
            "message": "Foto atualizada com sucesso!",
            "foto_perfil": updated["foto_perfil"] if updated else None
        }), 200
    except Exception as e:
        return jsonify({"error": "SERVER_ERROR", "message": "Erro ao atualizar foto: " + str(e)}), 500
