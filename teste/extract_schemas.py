import os
import pandas as pd
import glob
from collections import defaultdict

def extract_schemas():
    directory = r'c:\Users\karen.xavier\Desktop\pluraal saas\enem_data'
    schemas = defaultdict(list)
    
    # Use glob to find all xlsx files recursively
    files = glob.glob(os.path.join(directory, '**', '*.xlsx'), recursive=True)
    
    for file in files:
        try:
            # Read only the first row to get the columns
            df = pd.read_excel(file, nrows=0)
            # Use a tuple of column names as the key
            cols = tuple(str(col).strip() for col in df.columns)
            schemas[cols].append(os.path.relpath(file, directory))
        except Exception as e:
            print(f"Error reading {file}: {e}")
            
    # Print the grouped schemas
    for idx, (cols, file_list) in enumerate(schemas.items()):
        print(f"=== SCHEMA {idx + 1} ===")
        print(f"Columns: {', '.join(cols)}")
        print("Files:")
        for f in file_list:
            print(f"  - {f}")
        print()

if __name__ == '__main__':
    extract_schemas()
