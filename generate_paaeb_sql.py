import os
import glob
import pandas as pd
from collections import defaultdict
import re
import unicodedata

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def sanitize_col_name(col):
    col = str(col).strip()
    # Remove accents
    col = remove_accents(col)
    col = re.sub(r'[^A-Za-z0-9]+', '_', col)
    col = col.strip('_').upper()
    if not col:
        return 'COLUMN_UNKNOWN'
    if col[0].isdigit():
        col = 'COL_' + col
    return col

def get_category_from_filename(filename):
    basename = os.path.basename(filename).lower()
    basename = remove_accents(basename)
    
    # Common categories based on user prompt and typical school data
    categories = ['adequacao', 'media', 'aluno', 'escola', 'turma', 'habilidade', 'proficiencia', 'participacao', 'questoes', 'gabarito']
    
    for cat in categories:
        if cat in basename:
            return cat.upper()
    return 'DADOS_GERAIS'

def generate_paaeb_sql():
    directory = r'G:\Meu Drive\Projeto Pluraal\Paaeb oficial\tabelas'
    
    print(f"Buscando arquivos em {directory}...")
    files = glob.glob(os.path.join(directory, '**', '*.*'), recursive=True)
    # Filter only excel and csv
    files = [f for f in files if f.endswith('.xlsx') or f.endswith('.xls') or f.endswith('.csv')]
    print(f"Encontrados {len(files)} arquivos.")

    # Group by (category, columns_tuple)
    schemas = defaultdict(list)
    
    for file in files:
        try:
            if file.endswith('.csv'):
                # Try different encodings and separators
                try:
                    df = pd.read_csv(file, nrows=0, sep=';', encoding='utf-8')
                    if len(df.columns) <= 1:
                        df = pd.read_csv(file, nrows=0, sep=',', encoding='utf-8')
                except:
                    df = pd.read_csv(file, nrows=0, sep=';', encoding='latin1')
            else:
                df = pd.read_excel(file, nrows=0)
                
            cols = tuple(str(col).strip() for col in df.columns)
            if len(cols) <= 1:
                # Might be empty or just 1 column garbage
                continue
                
            category = get_category_from_filename(file)
            schemas[(category, cols)].append(file)
        except Exception as e:
            print(f"Erro ao ler cabeçalhos de {file}: {e}")

    output_file = r'c:\Users\karen.xavier\Desktop\pluraal saas\Backend\database\paab_schema.sql'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("CREATE SCHEMA IF NOT EXISTS PAAB_PROV;\n\n")
        
        # Track indices per category to name them like ADEQUACAO_1, ADEQUACAO_2
        category_index = defaultdict(int)
        
        for (category, cols), file_list in schemas.items():
            category_index[category] += 1
            table_index = category_index[category]
            
            table_name = f"PAAB_PROV.TB_{category}_{table_index}"
            
            f.write(f"-- Referência de arquivos: {', '.join([os.path.basename(x) for x in file_list[:5]])}")
            if len(file_list) > 5:
                f.write(f" e mais {len(file_list) - 5} arquivos...")
            f.write("\n")
            
            f.write(f"CREATE TABLE {table_name} (\n")
            f.write("    ID_PROPRIO SERIAL PRIMARY KEY,\n")
            
            seen_cols = set()
            for i, raw_col in enumerate(cols):
                sanitized = sanitize_col_name(raw_col)
                if sanitized in seen_cols:
                    sanitized = f"{sanitized}_{i}"
                seen_cols.add(sanitized)
                f.write(f"    {sanitized} TEXT,\n")
                
            f.write("    DATA_INSERCAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n")
            f.write(");\n\n")

    print(f"\\nScript SQL gerado em: {output_file}")
    print(f"Total de tabelas únicas geradas: {len(schemas)}")

if __name__ == '__main__':
    generate_paaeb_sql()
