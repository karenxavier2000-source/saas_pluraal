from flask import Blueprint, jsonify
from Backend.database.connection import get_db_connection
from Backend.middleware.auth_middleware import login_required

enem_bp = Blueprint('enem', __name__, url_prefix='/api/enem')

@enem_bp.route('/dashboard', methods=['GET'])
@login_required(required_page='enem')
def get_dashboard_stats():
    # Retorna estatísticas reais/mocks para o painel ENEM
    try:
        # Aqui, futuramente faremos JOINs reais nas 34 tabelas
        # Por enquanto, retornamos uma estrutura rica para a UI premium
        
        data = {
            "kpis": {
                "total_redacoes": 145000,
                "media_global": 750.5,
                "nota_mil": 245,
                "fuga_tema": "1.2%"
            },
            "competencias_dist": [
                {"name": "Comp. 1 (Gramática)", "score": 140},
                {"name": "Comp. 2 (Tema/Estrutura)", "score": 160},
                {"name": "Comp. 3 (Argumentação)", "score": 150},
                {"name": "Comp. 4 (Coesão)", "score": 160},
                {"name": "Comp. 5 (Proposta)", "score": 140}
            ],
            "rankings": [
                {"escola": "Escola Modelo A", "media": 890, "posicao": 1},
                {"escola": "Colégio Beta", "media": 860, "posicao": 2},
                {"escola": "Instituto Gama", "media": 845, "posicao": 3},
                {"escola": "Liceu Delta", "media": 830, "posicao": 4},
                {"escola": "Centro Ômega", "media": 810, "posicao": 5}
            ]
        }
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
