import sys
from pathlib import Path
ROOT_DIR = Path(r"c:\Users\karen.xavier\Desktop\pluraal saas")
sys.path.insert(0, str(ROOT_DIR))
from Backend.database.connection import get_db_cursor

with get_db_cursor(commit=False) as cur:
    cur.execute('''SELECT "SIGLA_ASSOCIACAO", "ESCOLA" FROM pluraal.escolas_pluraal WHERE "SIGLA_UNIAO" ILIKE '%UNEB%' OR "SIGLA_UNIAO" ILIKE '%União Nordeste Brasileira%' ''')
    print("ESCOLAS NA UNEB:", [r['ESCOLA'] for r in cur.fetchall()])
