import psycopg2
import os
from dotenv import load_dotenv
load_dotenv('.env')

conn = psycopg2.connect(
    host=os.getenv('PGHOST'),
    port=os.getenv('PGPORT'),
    dbname=os.getenv('PGDATABASE'),
    user=os.getenv('PGUSER'),
    password=os.getenv('PGPASSWORD')
)

try:
    with conn.cursor() as cur:
        # Verify the tables were created
        print("Checking tables in schema 'enem_pluraal'...")
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'enem_pluraal'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        print(f"Found {len(tables)} tables created:")
        for t in tables:
            print(f" - {t[0]}")
            
except Exception as e:
    print(f"Error during execution: {e}")
finally:
    conn.close()
