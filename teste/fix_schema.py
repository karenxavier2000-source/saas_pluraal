import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('.env')

conn = psycopg2.connect(
    host=os.getenv('PGHOST'),
    port=os.getenv('PGPORT'),
    dbname=os.getenv('PGDATABASE'),
    user=os.getenv('PGUSER'),
    password=os.getenv('PGPASSWORD')
)
conn.autocommit = True
cur = conn.cursor()

# Get tables in paab_prov (lowercase)
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='paab_prov';")
tables = cur.fetchall()

print("Movendo tabelas para o schema correto...")
for t in tables:
    tname = t[0]
    # Move to the uppercase schema the user is looking at
    try:
        cur.execute(f'ALTER TABLE paab_prov.{tname} SET SCHEMA "PAAB_PROV";')
        print(f"  {tname} movida para \"PAAB_PROV\"")
    except Exception as e:
        print(f"Erro ao mover {tname}: {e}")

# Drop the empty lowercase schema
try:
    cur.execute("DROP SCHEMA paab_prov;")
    print("Schema paab_prov (minúsculo) removido.")
except:
    pass

conn.close()
