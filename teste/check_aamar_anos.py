import psycopg2, os
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

query = """
SELECT 
    a.ano, a.bimestre, COUNT(*)
FROM pluraal.aluno a
JOIN pluraal.escolas_pluraal e ON LOWER(TRIM(a.escola)) = LOWER(TRIM(e."ESCOLA"))
WHERE e."SIGLA_ASSOCIACAO" = 'AAMAR'
GROUP BY a.ano, a.bimestre
"""
cur.execute(query)
for r in cur.fetchall():
    print(r)
