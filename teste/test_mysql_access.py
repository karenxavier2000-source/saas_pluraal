import pymysql

def try_connect(user, pwd, db=None):
    try:
        conn = pymysql.connect(
            host="192.168.171.158",
            user=user,
            password=pwd,
            database=db,
            connect_timeout=5
        )
        print(f"[OK] Connectou com {user} no banco '{db}'!")
        if db is None:
            cur = conn.cursor()
            cur.execute("CREATE DATABASE IF NOT EXISTS pluraal CHARACTER SET utf8mb4;")
            print("  -> Schema 'pluraal' criado/verificado com sucesso!")
        conn.close()
        return True
    except Exception as e:
        print(f"[ERRO] {user} (db={db}): {e}")
        return False

print("Testando acessos MySQL...")
try_connect("root", "")
try_connect("root", "Mudar@123")
try_connect("ALBERT_PLURAAL", "Mudar@123", "plurall")
try_connect("PLURALL_albert", "Mudar@123", "plurall")
