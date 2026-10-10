import os
import psycopg2
import json
import unicodedata
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

def normalize(text):
    if not text: return ""
    text = text.replace('–', '-').replace('—', '-')
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return text.lower().strip()

# Valid schools
cur.execute('SELECT id_escolas, "ESCOLA" FROM pluraal.escolas_pluraal WHERE "ESCOLA" IS NOT NULL')
valid_schools = {normalize(row[1]): row[1] for row in cur.fetchall()}

# Missing from PAAEB
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

mapping = {}
for ms in missing_schools:
    norm_ms = normalize(ms)
    
    # Custom hardcoded fixes for known patterns
    if "iaai" in norm_ms and "amazonas" in norm_ms: norm_ms = "colegio adventista amazonas - campus residencial - iaai"
    if "iaesc" in norm_ms: norm_ms = "iaesc - instituto adventista de ensino de santa catarina"
    if "iabc" in norm_ms or "brasil central" in norm_ms: norm_ms = "iabc - instituto adventista brasil central"
    if "unasp" in norm_ms and "engenheiro coelho" in norm_ms: norm_ms = "colegio unasp - engenheiro coelho"
    if "unasp" in norm_ms and "hortolandia" in norm_ms: norm_ms = "colegio unasp - hortolandia"
    if "unasp" in norm_ms and "sao paulo" in norm_ms: norm_ms = "colegio unasp - sao paulo"
    if "bom retiro" in norm_ms and "curitiba" in norm_ms: norm_ms = "colegio adventista bom retiro"

    # direct match
    if norm_ms in valid_schools:
        mapping[ms] = valid_schools[norm_ms]
        continue
        
    # try partial
    matched = False
    for v_norm, v_real in valid_schools.items():
        if norm_ms == v_norm:
            mapping[ms] = v_real
            matched = True
            break
    
    if not matched:
        # manual matching or partial
        # Find close matches manually
        import difflib
        matches = difflib.get_close_matches(norm_ms, valid_schools.keys(), n=1, cutoff=0.7)
        if matches:
            mapping[ms] = valid_schools[matches[0]]
        else:
            mapping[ms] = None

with open("school_mapping.json", "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"Mapped {len([m for m in mapping.values() if m])} out of {len(missing_schools)} missing schools.")
