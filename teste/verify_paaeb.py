import os
import glob
import pandas as pd
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

base_dir = r"G:\Meu Drive\Projeto Pluraal\Paaeb oficial\tabelas"

file_patterns = {
    'TB_ALUNO_1': ['DISTRIBUICAO_ALUNO*.xlsx', 'DISTRIBUICAO_ALUNO*.csv'],
    'TB_ADEQUACAO_1': ['ADEQUACAO*.xlsx', 'ADEQUACAO*.csv'],
    'TB_ADEQUACAO_2': ['ADEQUACAO_1_0*.xlsx', 'ADEQUACAO_1_0*.csv'],
    'TB_MEDIA_1': ['MEDIA_PROFICIENCIA*.xlsx', 'MEDIA_PROFICIENCIA*.csv'],
    'TB_DADOS_GERAIS_1': ['DISTRIBUIÇÃO*.xlsx', 'DISTRIBUIÇÃO*.csv'],
    'TB_PROFICIENCIA_1': ['PROFICIENCIA*.xlsx', 'PROFICIENCIA*.csv']
}

# The files in ADEQUACAO_1_0 should not be double counted in ADEQUACAO, 
# but usually ADEQUACAO* matches ADEQUACAO_1_0 as well if we just do ADEQUACAO*. 
# Actually, ADEQUACAO.xlsx usually.

def count_file_rows(filepath):
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        return len(df)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return 0

for table, patterns in file_patterns.items():
    print(f"\nVerificando tabela: {table}")
    
    # query DB
    try:
        cur = conn.cursor()
        cur.execute(f'SELECT COUNT(*) FROM "PAAB_PROV".{table.lower()};')
        db_count = cur.fetchone()[0]
        print(f"Registros no DB ({table}): {db_count}")
    except Exception as e:
        print(f"Erro ao acessar tabela {table}: {e}")
        conn.rollback()
        continue
    
    # Count files
    file_count = 0
    matched_files = []
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            is_match = False
            for pat in patterns:
                import fnmatch
                if fnmatch.fnmatch(file.lower(), pat.lower()):
                    is_match = True
                    # Exception: ADEQUACAO vs ADEQUACAO_1_0
                    if table == 'TB_ADEQUACAO_1' and 'adequacao_1_0' in file.lower():
                        is_match = False
                    break
            
            if is_match:
                filepath = os.path.join(root, file)
                matched_files.append(filepath)
                rows = count_file_rows(filepath)
                file_count += rows
                print(f"Arquivo: {filepath} | Linhas: {rows}")
                
    print(f"Total de registros nos arquivos ({table}): {file_count}")
    print(f"Diferença: {db_count - file_count}")
