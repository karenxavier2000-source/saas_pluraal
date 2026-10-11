import pymysql

def try_connect(user, pwd, host, db=None):
    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=pwd,
            database=db,
            connect_timeout=5
        )
        print(f"[OK] Connectou com {user}@{host}!")
        if db is None:
            cur = conn.cursor()
            cur.execute("CREATE DATABASE IF NOT EXISTS pluraal CHARACTER SET utf8mb4;")
            print("  -> Schema 'pluraal' criado com sucesso!")
        conn.close()
    except Exception as e:
        print(f"[ERRO] {user}@{host}: {e}")

print("Testando root local...")
try_connect("root", "Mudar@123", "127.0.0.1")
try_connect("root", "Mudar@123", "localhost")
