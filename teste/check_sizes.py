import psycopg

def check():
    conn = psycopg.connect(
        host="192.168.171.158",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="Mudar@123"
    )
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'pluraal';")
    tables = cur.fetchall()
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM pluraal.{t[0]};")
        count = cur.fetchone()[0]
        print(f"Tabela {t[0]}: {count} linhas")

if __name__ == "__main__":
    check()
