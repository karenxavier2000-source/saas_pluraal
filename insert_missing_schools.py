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

# Get missing schools and their Uniao/Associacao from tb_aluno_1
cur.execute("""
    SELECT DISTINCT p.escola, p.sigla_uniao, p.sigla_associacao
    FROM "PAAB_PROV".tb_aluno_1 p
    LEFT JOIN pluraal.escolas_pluraal e
      ON LOWER(TRIM(e."ESCOLA")) = CASE
          WHEN LOWER(TRIM(p.escola)) = LOWER('Instituto Adventista de Ensino de Santa Catarina (IAESC)')
          THEN LOWER('IAESC - Instituto Adventista de Ensino de Santa Catarina')
          ELSE LOWER(TRIM(p.escola)) END
    WHERE e.id_escolas IS NULL AND p.escola IS NOT NULL
""")
missing = cur.fetchall()

print(f"Encontradas {len(missing)} escolas para inserir.")

inserted = 0
for escola, uniao, assoc in missing:
    try:
        # PAAEB uniao and associacao formats: Usually string. 
        # Check if they exist in escolas_pluraal columns:
        cur.execute("""
            INSERT INTO pluraal.escolas_pluraal ("SIGLA_UNIAO", "SIGLA_ASSOCIACAO", "ESCOLA")
            VALUES (%s, %s, %s)
        """, (uniao, assoc, escola))
        inserted += cur.rowcount
    except Exception as e:
        print(f"Erro ao inserir {escola}: {e}")

conn.commit()
print(f"Sucesso: {inserted} escolas inseridas em pluraal.escolas_pluraal.")
