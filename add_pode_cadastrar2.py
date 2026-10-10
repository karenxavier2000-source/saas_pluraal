import psycopg
from Backend.config.settings import settings

def get_connection_params():
    return {
        "host": settings.PGHOST,
        "port": settings.PGPORT,
        "dbname": settings.PGDATABASE,
        "user": settings.PGUSER,
        "password": settings.PGPASSWORD,
        "options": f"-c search_path={settings.PGSCHEMA},public"
    }

try:
    with psycopg.connect(**get_connection_params(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                ALTER TABLE pluraal.usuario 
                ADD COLUMN IF NOT EXISTS pode_cadastrar_escola BOOLEAN DEFAULT FALSE;
            ''')
            cur.execute('''
                UPDATE pluraal.usuario 
                SET pode_cadastrar_escola = TRUE
                WHERE hierarquia = 'Master';
            ''')
    print('DB column updated successfully.')
except Exception as e:
    print('Error:', e)
