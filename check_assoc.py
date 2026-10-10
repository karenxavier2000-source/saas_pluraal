import psycopg2, os
from dotenv import load_dotenv
load_dotenv('.env')
conn=psycopg2.connect(host=os.getenv('PGHOST'), port=os.getenv('PGPORT'), dbname=os.getenv('PGDATABASE'), user=os.getenv('PGUSER'), password=os.getenv('PGPASSWORD'))
cur=conn.cursor()
cur.execute('SELECT DISTINCT "ASSOCIACAO" FROM pluraal.escolas_pluraal')
for r in cur.fetchall():
    print(r)
