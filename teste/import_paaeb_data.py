import os
import glob
import pandas as pd
from collections import defaultdict
import re
import unicodedata
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def sanitize_col_name(col):
    col = str(col).strip()
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
    categories = ['adequacao', 'media', 'aluno', 'escola', 'turma', 'habilidade', 'proficiencia', 'participacao', 'questoes', 'gabarito']
    for cat in categories:
        if cat in basename:
            return cat.upper()
    return 'DADOS_GERAIS'

def import_paaeb_data():
    load_dotenv('.env')
    conn = psycopg2.connect(
        host=os.getenv('PGHOST'),
        port=os.getenv('PGPORT'),
        dbname=os.getenv('PGDATABASE'),
        user=os.getenv('PGUSER'),
        password=os.getenv('PGPASSWORD')
    )
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            # Skip creating tables, just gather files and insert
            directory = r'G:\Meu Drive\Projeto Pluraal\Paaeb oficial\tabelas'
            files = glob.glob(os.path.join(directory, '**', '*.*'), recursive=True)
            files = [f for f in files if f.endswith('.xlsx') or f.endswith('.xls') or f.endswith('.csv')]
            
            schemas = defaultdict(list)
            for file in files:
                try:
                    if file.endswith('.csv'):
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
                        continue
                    category = get_category_from_filename(file)
                    schemas[(category, cols)].append(file)
                except Exception as e:
                    pass

            category_index = defaultdict(int)
            total_inserted = 0

            for (category, cols), file_list in schemas.items():
                category_index[category] += 1
                table_name = f"PAAB_PROV.TB_{category}_{category_index[category]}"
                print(f"Importando para {table_name}...")
                
                seen_cols = set()
                db_cols = []
                for i, raw_col in enumerate(cols):
                    sanitized = sanitize_col_name(raw_col)
                    if sanitized in seen_cols:
                        sanitized = f"{sanitized}_{i}"
                    seen_cols.add(sanitized)
                    db_cols.append(sanitized)
                
                col_names_str = ", ".join(db_cols)
                
                for file in file_list:
                    print(f"  Lendo {os.path.basename(file)}")
                    try:
                        if file.endswith('.csv'):
                            try:
                                df = pd.read_csv(file, sep=';', encoding='utf-8')
                                if len(df.columns) <= 1:
                                    df = pd.read_csv(file, sep=',', encoding='utf-8')
                            except:
                                df = pd.read_csv(file, sep=';', encoding='latin1')
                        else:
                            df = pd.read_excel(file)
                        
                        df = df.astype(object).where(pd.notnull(df), None)
                        for col in df.columns:
                            df[col] = df[col].apply(lambda x: str(x) if x is not None else None)
                        
                        records = [tuple(row) for row in df.itertuples(index=False, name=None)]
                        if not records:
                            continue
                        
                        insert_query = f"INSERT INTO {table_name} ({col_names_str}) VALUES %s"
                        execute_values(cur, insert_query, records, page_size=5000)
                        total_inserted += len(records)
                    except Exception as e:
                        print(f"  Erro ao inserir {file}: {e}")
            
            print(f"Importação PAAEB concluída! {total_inserted} linhas inseridas no total.")

    except Exception as e:
        print(f"Erro fatal: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    import_paaeb_data()
