import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
from Backend.config.settings import settings

def get_connection_params():
    return {
        "host": settings.PGHOST,
        "port": settings.PGPORT,
        "dbname": settings.PGDATABASE,
        "user": settings.PGUSER,
        "password": settings.PGPASSWORD,
        "row_factory": dict_row,
        "options": f"-c search_path={settings.PGSCHEMA},public"
    }

@contextmanager
def get_db_connection():
    conn = psycopg.connect(**get_connection_params())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

@contextmanager
def get_db_cursor(commit=True):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            yield cur
            if commit:
                conn.commit()
