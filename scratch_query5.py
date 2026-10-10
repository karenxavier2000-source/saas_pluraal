import sys
from pathlib import Path
ROOT_DIR = Path(r"c:\Users\karen.xavier\Desktop\pluraal saas")
sys.path.insert(0, str(ROOT_DIR))
from Backend.database.connection import get_db_cursor

with get_db_cursor(commit=False) as cur:
    cur.execute("SELECT DISTINCT school_key FROM attempts WHERE nome ILIKE '%Simulado de LINGUAGENS E CÓDIGOS%'")
    print("SCHOOLS IN ATTEMPTS FOR THIS SIMULADO:")
    for r in cur.fetchall():
        print(r['school_key'])
