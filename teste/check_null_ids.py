import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env')

conn = psycopg2.connect(
    host=os.getenv('PGHOST'),
    port=os.getenv('PGPORT'),
    dbname=os.getenv('PGDATABASE'),
    user=os.getenv('PGUSER'),
    password=os.getenv('PGPASSWORD')
)
cur = conn.cursor()

cur.execute('SELECT "ESCOLA" FROM pluraal.escolas_pluraal WHERE id_escolas IS NULL')
null_ids = cur.fetchall()
print(f"Schools with NULL id_escolas: {len(null_ids)}")

if len(null_ids) > 0:
    cur.execute('SELECT COALESCE(MAX(id_escolas), 0) FROM pluraal.escolas_pluraal')
    max_id = cur.fetchone()[0]
    for row in null_ids:
        max_id += 1
        cur.execute('UPDATE pluraal.escolas_pluraal SET id_escolas = %s WHERE "ESCOLA" = %s AND id_escolas IS NULL', (max_id, row[0]))
    conn.commit()
    print("Fixed NULL ids!")
