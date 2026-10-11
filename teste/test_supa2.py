import psycopg
import sys

def test_supabase():
    try:
        conn = psycopg.connect(
            host="aws-1-us-west-2.pooler.supabase.com",
            port=6543,
            dbname="postgres",
            user="postgres.xlptaftgfxogvmebqzoy",
            password="0Utl@nd&r2001",
            connect_timeout=10
        )
        print("SUPABASE CONNECTED SUCCESSFULLY!")
        
        # Enable uuid-ossp just in case
        cur = conn.cursor()
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        
        # Create schema if not exists
        cur.execute('CREATE SCHEMA IF NOT EXISTS pluraal;')
        conn.commit()
        print("SCHEMA 'pluraal' CREATED/VERIFIED!")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"SUPABASE CONNECTION FAILED: {e}")
        return False

def test_local():
    try:
        conn = psycopg.connect(
            host="192.168.171.158",
            port=5432,
            dbname="postgres",
            user="postgres",
            password="Mudar@123",
            connect_timeout=10
        )
        print("LOCAL POSTGRES CONNECTED SUCCESSFULLY!")
        
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'pluraal';")
        tables = cur.fetchall()
        print(f"FOUND {len(tables)} TABLES IN LOCAL SCHEMA 'pluraal'")
        for t in tables:
            print(f"- {t[0]}")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"LOCAL CONNECTION FAILED: {e}")
        return False

if __name__ == "__main__":
    print("Testing connections...")
    s = test_supabase()
    l = test_local()
    if s and l:
        print("AMBOS CONECTADOS!")
    else:
        sys.exit(1)
