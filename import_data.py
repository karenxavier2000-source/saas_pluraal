import os
import pandas as pd
import glob
from collections import defaultdict
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import re

def sanitize_col_name(col):
    col = str(col).strip()
    col = re.sub(r'[^A-Za-z0-9]+', '_', col)
    col = col.strip('_').upper()
    if not col:
        return 'COLUMN_UNKNOWN'
    if col[0].isdigit():
        col = 'COL_' + col
    return col

def get_db_connection():
    load_dotenv('.env')
    return psycopg2.connect(
        host=os.getenv('PGHOST'),
        port=os.getenv('PGPORT'),
        dbname=os.getenv('PGDATABASE'),
        user=os.getenv('PGUSER'),
        password=os.getenv('PGPASSWORD')
    )

def import_data():
    directory = r'c:\Users\karen.xavier\Desktop\pluraal saas\enem_data'
    schemas = defaultdict(list)
    
    print("Mapeando arquivos...")
    files = glob.glob(os.path.join(directory, '**', '*.xlsx'), recursive=True)
    
    for file in files:
        try:
            df = pd.read_excel(file, nrows=0)
            cols = tuple(str(col).strip() for col in df.columns)
            if len(cols) <= 1:
                continue
            schemas[cols].append(file)
        except Exception as e:
            print(f"Erro ao ler cabeçalhos de {file}: {e}")

    conn = get_db_connection()
    conn.autocommit = True
    
    table_index = 1
    total_rows_inserted = 0

    try:
        with conn.cursor() as cur:
            for cols, file_list in schemas.items():
                table_name = f"ENEM_PLURAAL.TB_ENEM_DADOS_{table_index}"
                print(f"\\n--- Importando para {table_name} ---")
                
                # Resolvendo nomes das colunas exatamente como no generate_sql
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
                    print(f"Lendo {os.path.basename(file)}...")
                    try:
                        # Lê os dados
                        df = pd.read_excel(file)
                        
                        # Preenche NaN com None
                        df = df.astype(object).where(pd.notnull(df), None)
                        
                        # Converte todas as colunas para string (quando não for None) para bater com o TEXT do banco
                        for col in df.columns:
                            df[col] = df[col].apply(lambda x: str(x) if x is not None else None)
                            
                        # Preparar os registros como uma lista de tuplas
                        records = [tuple(row) for row in df.itertuples(index=False, name=None)]
                        
                        if not records:
                            continue
                            
                        # Insert em batch
                        insert_query = f"INSERT INTO {table_name} ({col_names_str}) VALUES %s"
                        execute_values(cur, insert_query, records, page_size=5000)
                        
                        total_rows_inserted += len(records)
                        print(f"  -> {len(records)} linhas inseridas.")
                        
                    except Exception as e:
                        print(f"Erro ao importar arquivo {file}: {e}")
                
                table_index += 1
                
        print(f"\\n✅ Importação concluída com sucesso! Total de linhas inseridas: {total_rows_inserted}")
    except Exception as e:
        print(f"Erro na execução da importação: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    import_data()
