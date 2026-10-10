from flask import Blueprint, request, jsonify, g
from Backend.services.auth_service import authenticate_user, change_user_password
from Backend.services.user_service import get_user_by_id
from Backend.middleware.auth_middleware import login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    senha = data.get("senha", "")

    if not email or not senha:
        return jsonify({"error": "VALIDATION_ERROR", "message": "E-mail e senha são obrigatórios."}), 400

    try:
        result = authenticate_user(email, senha)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": "INVALID_CREDENTIALS", "message": str(e)}), 401
    except PermissionError as e:
        code = "LOGIN_EXPIRED" if str(e).startswith("O prazo de acesso") else "USER_INACTIVE"
        return jsonify({"error": code, "message": str(e)}), 403
    except Exception as e:
        return jsonify({"error": "SERVER_ERROR", "message": "Erro ao processar login: " + str(e)}), 500

@auth_bp.route("/change-password", methods=["POST"])
@login_required(allow_pending_password_change=True)
def change_password():
    data = request.get_json(silent=True) or {}
    senha_atual = data.get("senha_atual", "")
    nova_senha = data.get("nova_senha", "")
    confirmacao_senha = data.get("confirmacao_senha", "")

    try:
        user_id = g.current_user["id_usuario"]
        result = change_user_password(user_id, senha_atual, nova_senha, confirmacao_senha)
        return jsonify({
            "message": "Senha alterada com sucesso! O acesso completo ao sistema foi liberado.",
            **result
        }), 200
    except ValueError as e:
        return jsonify({"error": "VALIDATION_ERROR", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "SERVER_ERROR", "message": "Erro ao alterar senha: " + str(e)}), 500

@auth_bp.route("/me", methods=["GET"])
@login_required(allow_pending_password_change=True)
def get_current_user_profile():
    user = get_user_by_id(g.current_user["id_usuario"])
    return jsonify(user), 200

@auth_bp.route("/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Logout realizado com sucesso."}), 200
