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

# 1. Total distinct students in 5th grade WITHOUT JOIN
cur.execute("""
    SELECT COUNT(DISTINCT (LOWER(TRIM(escola)), LOWER(TRIM(nome_aluno)))) AS alunos
    FROM "PAAB_PROV".tb_aluno_1
    WHERE TRIM(serie) = '5º ano'
""")
total_alunos_5 = cur.fetchone()[0]

# 2. Total distinct students in 5th grade WITH JOIN
cur.execute("""
    SELECT COUNT(DISTINCT (LOWER(TRIM(p.escola)), LOWER(TRIM(p.nome_aluno)))) AS alunos
    FROM "PAAB_PROV".tb_aluno_1 p
    JOIN pluraal.escolas_pluraal e
      ON LOWER(TRIM(e."ESCOLA")) = CASE
          WHEN LOWER(TRIM(p.escola)) = LOWER('Instituto Adventista de Ensino de Santa Catarina (IAESC)')
          THEN LOWER('IAESC - Instituto Adventista de Ensino de Santa Catarina')
          ELSE LOWER(TRIM(p.escola)) END
    WHERE TRIM(p.serie) = '5º ano'
""")
total_alunos_5_join = cur.fetchone()[0]

print(f"Alunos (5º ano) SEM JOIN: {total_alunos_5}")
print(f"Alunos (5º ano) COM JOIN: {total_alunos_5_join}")

# 3. Check what schools are failing the join
cur.execute("""
    SELECT DISTINCT p.escola
    FROM "PAAB_PROV".tb_aluno_1 p
    LEFT JOIN pluraal.escolas_pluraal e
      ON LOWER(TRIM(e."ESCOLA")) = CASE
          WHEN LOWER(TRIM(p.escola)) = LOWER('Instituto Adventista de Ensino de Santa Catarina (IAESC)')
          THEN LOWER('IAESC - Instituto Adventista de Ensino de Santa Catarina')
          ELSE LOWER(TRIM(p.escola)) END
    WHERE e.id_escolas IS NULL
""")
missing_schools = cur.fetchall()
print(f"\nEscolas que NÃO estão fazendo match ({len(missing_schools)}):")
for s in missing_schools:
    print(s[0])
