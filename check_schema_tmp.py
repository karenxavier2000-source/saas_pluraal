from Backend.database.connection import get_db_cursor
with get_db_cursor(commit=False) as cur:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'pluraal' AND table_name = 'usuario'")
    print("usuario:", cur.fetchall())
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'pluraal' AND table_name = 'usuario_acesso'")
    print("usuario_acesso:", cur.fetchall())
