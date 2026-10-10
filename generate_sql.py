import os
import pandas as pd
import glob
from collections import defaultdict
import re

def sanitize_col_name(col):
    col = str(col).strip()
    # Replace anything that isn't alphanumeric with an underscore
    col = re.sub(r'[^A-Za-z0-9]+', '_', col)
    # Remove leading/trailing underscores
    col = col.strip('_').upper()
    # If the column name is empty or starts with a number, add a prefix
    if not col:
        return 'COLUMN_UNKNOWN'
    if col[0].isdigit():
        col = 'COL_' + col
    return col

def generate_sql():
    directory = r'c:\Users\karen.xavier\Desktop\pluraal saas\enem_data'
    schemas = defaultdict(list)
    
    files = glob.glob(os.path.join(directory, '**', '*.xlsx'), recursive=True)
    
    for file in files:
        try:
            df = pd.read_excel(file, nrows=0)
            cols = tuple(str(col).strip() for col in df.columns)
            # Skip if only 1 column and it looks like a title row
            if len(cols) <= 1:
                continue
            schemas[cols].append(file)
        except Exception as e:
            print(f"Error reading {file}: {e}")
            
    sql_lines = []
    sql_lines.append("CREATE SCHEMA IF NOT EXISTS ENEM_PLURAAL;")
    sql_lines.append("")
    
    table_index = 1
    
    for cols, file_list in schemas.items():
        table_name = f"ENEM_PLURAAL.TB_ENEM_DADOS_{table_index}"
        
        # Adding comment to know which files correspond to this table
        filenames = [os.path.basename(f) for f in file_list][:3] # list up to 3 files
        sql_lines.append(f"-- Referência de arquivos: {', '.join(filenames)}")
        
        sql_lines.append(f"CREATE TABLE {table_name} (")
        sql_lines.append("    ID_PROPRIO SERIAL PRIMARY KEY,")
        
        seen_cols = set()
        for i, raw_col in enumerate(cols):
            sanitized = sanitize_col_name(raw_col)
            # handle duplicate column names after sanitization
            if sanitized in seen_cols:
                sanitized = f"{sanitized}_{i}"
            seen_cols.add(sanitized)
            
            sql_lines.append(f"    {sanitized} TEXT,")
            
        sql_lines.append("    DATA_INSERCAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        sql_lines.append(");")
        sql_lines.append("")
        
        table_index += 1
        
    out_path = r'c:\Users\karen.xavier\Desktop\pluraal saas\Backend\database\enem_schema.sql'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
        
    print(f"Generated SQL for {table_index - 1} unique schemas at {out_path}")

if __name__ == '__main__':
    generate_sql()
