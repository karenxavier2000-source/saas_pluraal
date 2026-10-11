import psycopg

def test_supabase():
    try:
        conn = psycopg.connect(
            host="aws-0-us-east-1.pooler.supabase.com",
            port=5432,
            dbname="postgres",
            user="postgres",
            password="0Utl@nd&r2001",
            connect_timeout=5
        )
        print("CONECTADO NA PORTA 5432 COM SUCESSO!")
        conn.close()
    except Exception as e:
        print(f"FALHA NA PORTA 5432: {e}")

    try:
        conn = psycopg.connect(
            host="aws-0-us-east-1.pooler.supabase.com",
            port=6543,
            dbname="postgres",
            user="postgres.xwqllkbwtverxtxmqolb",
            password="0Utl@nd&r2001",
            connect_timeout=5
        )
        print("CONECTADO NA PORTA 6543 COM SUCESSO!")
        conn.close()
    except Exception as e:
        print(f"FALHA NA PORTA 6543: {e}")

if __name__ == "__main__":
    test_supabase()
