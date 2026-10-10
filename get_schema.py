import json
from Backend.database.connection import get_db_cursor

try:
    with get_db_cursor(commit=False) as cur:
        cur.execute('''
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'pluraal' AND table_name = 'escolas_pluraal';
        ''')
        rows = cur.fetchall()
        for r in rows:
            print(r['column_name'], r['data_type'])
except Exception as e:
    print('Error:', e)
