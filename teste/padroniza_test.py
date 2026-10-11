import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST'),
    port=int(os.getenv('MYSQL_PORT', 3306)),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DB')
)

cursor = conn.cursor(dictionary=True)

tabelas = ['mapa_simulados', 'questao_simulado', 'simulados']

for tabela in tabelas:
    print(f"\nAtualizando {tabela}...")
    # This query joins on the default case-insensitive collation, 
    # but filters for rows where the exact binary casing is different.
    # It updates the target table with the exact casing from escolas_pluraal.
    query = f"""
    UPDATE {tabela} t
    JOIN escolas_pluraal e ON t.escola = e.escola
    SET t.escola = e.escola
    WHERE t.escola COLLATE utf8mb4_bin != e.escola COLLATE utf8mb4_bin
    """
    cursor.execute(query)
    conn.commit()
    print(f"Linhas afetadas em {tabela}: {cursor.rowcount}")

cursor.close()
conn.close()
