from flask import Blueprint, jsonify, request, g
from Backend.services.school_service import (
    list_schools, create_school, update_school, delete_school
)
from Backend.middleware.auth_middleware import login_required

bp = Blueprint('schools', __name__)


def _master_only():
    return g.current_user['hierarquia'] == 'Master'

@bp.route('', methods=['GET'])
@login_required()
def handle_list_schools():
    if not _master_only():
        return jsonify({'message': 'Acesso restrito ao usuário Master.'}), 403
    return jsonify(list_schools())

@bp.route('', methods=['POST'])
@login_required()
def handle_create_school():
    if not _master_only():
        return jsonify({'message': 'Acesso restrito ao usuário Master.'}), 403
    
    data = request.get_json(silent=True) or {}
    try:
        new_id = create_school(data)
        return jsonify({"message": "Escola cadastrada", "id": new_id}), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@bp.route('/<int:school_id>', methods=['PUT'])
@login_required()
def handle_update_school(school_id):
    if not _master_only():
        return jsonify({'message': 'Acesso restrito ao usuário Master.'}), 403
    
    data = request.get_json(silent=True) or {}
    try:
        update_school(school_id, data)
        return jsonify({"message": "Escola atualizada"})
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@bp.route('/<int:school_id>', methods=['DELETE'])
@login_required()
def handle_delete_school(school_id):
    if not _master_only():
        return jsonify({'message': 'Acesso restrito ao usuário Master.'}), 403
    
    try:
        delete_school(school_id)
        return jsonify({"message": "Escola excluída"})
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
