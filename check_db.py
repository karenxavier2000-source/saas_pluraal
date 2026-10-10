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

cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='pluraal';")
tables = cur.fetchall()
print("Tabelas no schema pluraal:")
for t in tables:
    print(t[0])

# Also check paab_prov in lowercase vs uppercase
cur.execute("SELECT schema_name FROM information_schema.schemata;")
schemas = cur.fetchall()
print("Schemas no DB:")
for s in schemas:
    if 'paab' in s[0].lower() or 'paaeb' in s[0].lower():
        print(s[0])
