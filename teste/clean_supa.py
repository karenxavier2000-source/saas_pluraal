import psycopg

def clean_supabase():
    print("Conectando ao Supabase para limpar o schema...")
    conn = psycopg.connect(
        host="aws-1-us-west-2.pooler.supabase.com",
        port=6543,
        dbname="postgres",
        user="postgres.xlptaftgfxogvmebqzoy",
        password="0Utl@nd&r2001",
        connect_timeout=10
    )
    cur = conn.cursor()
    cur.execute("DROP SCHEMA IF EXISTS pluraal CASCADE;")
    cur.execute("CREATE SCHEMA pluraal;")
    conn.commit()
    print("Schema 'pluraal' limpo no Supabase!")

if __name__ == "__main__":
    clean_supabase()
