import psycopg
import sys

def test_supabase():
    try:
        conn = psycopg.connect(
            host="aws-0-us-east-1.pooler.supabase.com",
            port=6543,
            dbname="postgres",
            user="postgres.xwqllkbwtverxtxmqolb",
            password="0Utl@nd&r2001",
            connect_timeout=10
        )
        print("SUPABASE CONNECTED SUCCESSFULLY!")
        conn.close()
        return True
    except Exception as e:
        print(f"SUPABASE CONNECTION FAILED: {e}")
        return False

if __name__ == "__main__":
    test_supabase()
