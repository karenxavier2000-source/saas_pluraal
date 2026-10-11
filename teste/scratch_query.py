import sys
from pathlib import Path

ROOT_DIR = Path(r"c:\Users\karen.xavier\Desktop\pluraal saas")
sys.path.insert(0, str(ROOT_DIR))

from Backend.database.connection import get_db_cursor

with get_db_cursor(commit=False) as cur:
    cur.execute("SELECT DISTINCT id_simulado, escola, ra, alunos FROM pluraal.gabarito_aluno WHERE alunos ILIKE '%Maria Fernanda Diniz da Paz Ezaquiel%'")
    print("GABARITO ALUNO EXACT NAME:", cur.fetchall())
    
    cur.execute("SELECT DISTINCT id_simulado, escola, ra, alunos FROM pluraal.gabarito_aluno WHERE alunos ILIKE '%Maria Fernanda%' AND escola ILIKE '%Pessoa%'")
    print("GABARITO ALUNO PARTIAL NAME AND SCHOOL:", cur.fetchall())
