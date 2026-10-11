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

cur.execute('''SELECT "ESCOLA" FROM pluraal.escolas_pluraal 
               WHERE "ESCOLA" ILIKE '%cascavel%' 
                  OR "ESCOLA" ILIKE '%pelotas%' 
                  OR "ESCOLA" ILIKE '%afonso pena%' ''')
print(cur.fetchall())
