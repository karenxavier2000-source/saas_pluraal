import sys
sys.path.insert(0, '.')
from Backend.database.connection import get_db_cursor
with get_db_cursor(commit=True) as cur:
    cur.execute('DELETE FROM pluraal.escolas_pluraal WHERE "SIGLA_ASSOCIACAO"=\'MTO\' AND "SIGLA_UNIAO"=\'UCOB\'')
    print('Deleted rows:', cur.rowcount)
