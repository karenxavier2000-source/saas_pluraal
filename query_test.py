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

query = """
SELECT total_final, total_acertos, total_questao, nota_disciplina
FROM pluraal.aluno
WHERE total_final IS NOT NULL
LIMIT 10;
"""
cur.execute(query)
for r in cur.fetchall():
    print(r)
