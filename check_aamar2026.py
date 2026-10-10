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
    COUNT(*), 
    COUNT(a.total_final) cnt_total_final, 
    AVG(a.total_final) avg_total_final, 
    AVG(a.total_acertos::float/NULLIF(a.total_questao,0)*100) avg_pct
FROM pluraal.aluno a
JOIN pluraal.escolas_pluraal e ON LOWER(TRIM(a.escola)) = LOWER(TRIM(e."ESCOLA"))
WHERE e."SIGLA_ASSOCIACAO" = 'AAMAR'
  AND a.bimestre = '3º BIMESTRE'
  AND a.id_simulado IS NOT NULL
"""
cur.execute(query)
print(cur.fetchall())
