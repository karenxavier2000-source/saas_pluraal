import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL
import time

pg_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="Mudar@123",
    host="192.168.171.158",
    port=5432,
    database="postgres"
)

# Conectando como root no localhost
mysql_root_url = URL.create(
    drivername="mysql+pymysql",
    username="root",
    password="Mudar@123",
    host="127.0.0.1",
    port=3306
)

def migrate_schema(schema_name):
    print(f"\\n=== Iniciando migracao do schema: {schema_name} ===")
    pg_engine = create_engine(pg_url)
    
    # Garante que o schema existe no MySQL
    mysql_server_engine = create_engine(mysql_root_url)
    with mysql_server_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {schema_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
    
    mysql_db_url = URL.create(
        drivername="mysql+pymysql",
        username="root",
        password="Mudar@123",
        host="127.0.0.1",
        port=3306,
        database=schema_name
    )
    mysql_engine = create_engine(mysql_db_url)
    
    inspector = inspect(pg_engine)
    tables = inspector.get_table_names(schema=schema_name)
    print(f"Tabelas encontradas: {tables}")
    
    for table in tables:
        print(f"\\nMigrando tabela: {table}...")
        start = time.time()
        
        # Le tudo do postgres
        try:
            chunks = pd.read_sql_table(table, pg_engine, schema=schema_name, chunksize=50000)
            
            first = True
            total_rows = 0
            for chunk in chunks:
                # O Pandas lida com a criacao da tabela e adaptacao dos tipos (como Arrays virando strings)
                if first:
                    chunk.to_sql(table, mysql_engine, index=False, if_exists='replace')
                    first = False
                else:
                    chunk.to_sql(table, mysql_engine, index=False, if_exists='append')
                total_rows += len(chunk)
                print(f"  -> Copiadas {total_rows} linhas...", end="\\r")
            
            print(f"\\n  -> Tabela {table} finalizada em {time.time()-start:.1f} segundos!")
        except Exception as e:
            print(f"\\n  [ERRO] Falha ao migrar {table}: {e}")
            
if __name__ == "__main__":
    migrate_schema("pluraal")
    migrate_schema("paaeb")
    print("\\n\\nMIGRACAO TOTAL PARA O MYSQL FINALIZADA!")
