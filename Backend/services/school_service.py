from Backend.database.connection import get_db_cursor
from Backend.services.report_service import _REPORT_CACHE


FIELDS = ('UNIAO', 'SIGLA_UNIAO', 'ASSOCIACAO', 'SIGLA_ASSOCIACAO', 'ESCOLA')


def list_schools():
    with get_db_cursor(commit=False) as cur:
        cur.execute('''SELECT id_escolas, "UNIAO", "SIGLA_UNIAO", "ASSOCIACAO",
                              "SIGLA_ASSOCIACAO", "ESCOLA"
                       FROM pluraal.escolas_pluraal ORDER BY "ESCOLA", id_escolas''')
        return cur.fetchall()


def _validated(data):
    values = {field: str(data.get(field) or '').strip() for field in FIELDS}
    if not all(values.values()):
        raise ValueError('Preencha união, sigla da união, associação, sigla da associação e escola.')
    with get_db_cursor(commit=False) as cur:
        cur.execute('''SELECT 1 FROM pluraal.escolas_pluraal
                       WHERE TRIM("UNIAO")=%s AND TRIM("SIGLA_UNIAO")=%s
                         AND TRIM("ASSOCIACAO")=%s AND TRIM("SIGLA_ASSOCIACAO")=%s
                       LIMIT 1''', tuple(values[field] for field in FIELDS[:4]))
        if not cur.fetchone():
            raise ValueError('Selecione uma combinação de união e associação já cadastrada.')
    return values


def create_school(data):
    values = _validated(data)
    with get_db_cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(748219)')
        cur.execute('SELECT COALESCE(MAX(id_escolas), 0) + 1 AS id FROM pluraal.escolas_pluraal')
        new_id = cur.fetchone()['id']
        cur.execute('''INSERT INTO pluraal.escolas_pluraal
                       (id_escolas, "UNIAO", "SIGLA_UNIAO", "ASSOCIACAO", "SIGLA_ASSOCIACAO", "ESCOLA")
                       VALUES (%s, %s, %s, %s, %s, %s)''',
                    (new_id, *(values[field] for field in FIELDS)))
    _REPORT_CACHE.clear()
    return new_id


def update_school(school_id, data):
    values = _validated(data)
    with get_db_cursor() as cur:
        cur.execute('''UPDATE pluraal.escolas_pluraal SET "UNIAO"=%s, "SIGLA_UNIAO"=%s,
                       "ASSOCIACAO"=%s, "SIGLA_ASSOCIACAO"=%s, "ESCOLA"=%s
                       WHERE id_escolas=%s''',
                    (*(values[field] for field in FIELDS), school_id))
        if not cur.rowcount:
            raise ValueError('Escola não encontrada.')
    _REPORT_CACHE.clear()


def delete_school(school_id):
    with get_db_cursor() as cur:
        cur.execute('DELETE FROM pluraal.escolas_pluraal WHERE id_escolas=%s', (school_id,))
        if not cur.rowcount:
            raise ValueError('Escola não encontrada.')
    _REPORT_CACHE.clear()
