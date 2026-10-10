import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    port=int(os.getenv("MYSQL_PORT", 3306)),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DB")
)

cursor = conn.cursor(dictionary=True)

# List tables
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()
print("Tables in MySQL:", tables)

table_name = os.getenv("TABELA_SIMULADOS", "simualdos")
print(f"Checking table: {table_name}")

try:
    cursor.execute(f"SELECT COUNT(*) as cnt FROM {table_name} WHERE serie IS NULL OR serie = '' OR nivel IS NULL OR nivel = '' OR nivel_serie IS NULL OR nivel_serie = ''")
    row = cursor.fetchone()
    print(f"Records missing serie/nivel/nivel_serie: {row['cnt']}")

    cursor.execute(f"SELECT id, arquivo, serie, nivel, nivel_serie FROM {table_name} WHERE serie IS NULL OR serie = '' OR nivel IS NULL OR nivel = '' LIMIT 10")
    rows = cursor.fetchall()
    print("\nSample records:")
    for r in rows:
        print(r)
except Exception as e:
    print("Error querying:", e)

cursor.close()
conn.close()
