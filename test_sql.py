import psycopg2, os, dotenv
dotenv.load_dotenv('.env')
conn = psycopg2.connect(host=os.getenv('PGHOST'), port=os.getenv('PGPORT'), dbname=os.getenv('PGDATABASE'), user=os.getenv('PGUSER'), password=os.getenv('PGPASSWORD'))
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='pluraal' AND table_name='gabarito_aluno'")
print([r[0] for r in cur.fetchall()])
