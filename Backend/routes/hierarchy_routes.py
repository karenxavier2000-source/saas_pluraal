from flask import Blueprint, jsonify, g
from Backend.services.hierarchy_service import get_delegation_capabilities
from Backend.middleware.auth_middleware import login_required

hierarchy_bp = Blueprint("hierarchy", __name__, url_prefix="/api/hierarchy")

@hierarchy_bp.route("/capabilities", methods=["GET"])
@login_required()
def get_capabilities():
    try:
        user_id = g.current_user["id_usuario"]
        data = get_delegation_capabilities(user_id)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": "SERVER_ERROR", "message": str(e)}), 500
