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
    COUNT(a.nota_disciplina) as cnt_nota_disciplina,
    COUNT(a.qtd_acertos_disciplina) as cnt_acertos,
    COUNT(a.qtd_questao_disciplina) as cnt_questoes,
    SUM(a.qtd_acertos_disciplina) as sum_acertos,
    SUM(a.qtd_questao_disciplina) as sum_questoes
FROM pluraal.aluno a
JOIN pluraal.escolas_pluraal e ON LOWER(TRIM(a.escola)) = LOWER(TRIM(e."ESCOLA"))
WHERE e."SIGLA_ASSOCIACAO" = 'AAMAR'
  AND a.bimestre = '3º BIMESTRE'
  AND a.id_simulado IS NOT NULL
"""
cur.execute(query)
print(cur.fetchall())
