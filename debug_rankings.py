import os
from dotenv import load_dotenv
from Backend.services.report_service import get_reports_data
from Backend.services.delegation_service import get_effective_user_scope
from Backend.database.db_helper import get_db_cursor
from Backend.server import create_app

load_dotenv('.env')

user_id = 1
filters = {
    "ano": "2024",
    "bimestre": "3º BIMESTRE",
    "uniao": "Todas as uniões",
    "associacao": "AAMAR",
    "escola": "Todas as escolas"
}

try:
    app = create_app()
    with app.app_context():
        with get_db_cursor(commit=False) as cur:
            scope = get_effective_user_scope(user_id, cur)
            print("Scope Hierarquia:", scope.get('hierarquia'))
        data = get_reports_data(user_id, filters)
        print("Rankings Keys:", data.get('rankings', {}).keys())
        for i, rank in enumerate(data['rankings'].get('associacao', [])):
            print(f"{i+1} - {rank['nome']} ({rank['proprio']})")
except Exception as e:
    import traceback
    traceback.print_exc()
