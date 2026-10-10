import os
import psycopg2
import difflib
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

# Get all valid school names from escolas_pluraal
cur.execute('SELECT DISTINCT "ESCOLA" FROM pluraal.escolas_pluraal WHERE "ESCOLA" IS NOT NULL')
valid_schools = [row[0] for row in cur.fetchall()]

# Get missing schools
cur.execute("""
    SELECT DISTINCT p.escola
    FROM "PAAB_PROV".tb_aluno_1 p
    LEFT JOIN pluraal.escolas_pluraal e
      ON LOWER(TRIM(e."ESCOLA")) = CASE
          WHEN LOWER(TRIM(p.escola)) = LOWER('Instituto Adventista de Ensino de Santa Catarina (IAESC)')
          THEN LOWER('IAESC - Instituto Adventista de Ensino de Santa Catarina')
          ELSE LOWER(TRIM(p.escola)) END
    WHERE e.id_escolas IS NULL AND p.escola IS NOT NULL
""")
missing_schools = [row[0] for row in cur.fetchall()]

print(f"Missing schools: {len(missing_schools)}")
for ms in missing_schools:
    matches = difflib.get_close_matches(ms, valid_schools, n=1, cutoff=0.6)
    match_str = matches[0] if matches else "NO MATCH"
    print(f"PAAEB: {ms}\n  --> {match_str}\n")
