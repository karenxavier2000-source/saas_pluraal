import sys
from pathlib import Path
ROOT_DIR = Path(r"c:\Users\karen.xavier\Desktop\pluraal saas")
sys.path.insert(0, str(ROOT_DIR))
from Backend.database.connection import get_db_cursor
from Backend.services.delegation_service import get_effective_user_scope
from Backend.services.report_service import _catalog, _scope_rows

with get_db_cursor(commit=False) as cur:
    for uid in (34, 38, 44):
        try:
            scope = get_effective_user_scope(uid, cur)
            if scope:
                print(f"UID: {uid}, Hierarquia: {scope.get('hierarquia')}, Escolas Count: {len(scope.get('escolas', []))}")
                catalog = _catalog(cur)
                own, selected, preview = _scope_rows(catalog, scope, {'uniao': 'UNEB'})
                print(f"  Target UNEB schools: {[r['escola'] for r in selected]}")
            else:
                print(f"UID: {uid} has NO scope")
        except Exception as e:
            print(f"UID: {uid} Error: {e}")
