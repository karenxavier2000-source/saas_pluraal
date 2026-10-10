"""Exportação das tabelas brutas, sempre limitada ao acesso efetivo do usuário."""
import csv
import io
from datetime import date

from Backend.database.connection import get_db_connection, get_db_cursor
from Backend.services.delegation_service import get_effective_user_scope
from Backend.services.report_service import _catalog, _scope_rows

TABLES = {'aluno', 'gabarito_aluno'}


def _authorized_schools(user_id, filters):
    with get_db_cursor(commit=False) as cur:
        scope = get_effective_user_scope(user_id, cur, allow_simulation=True)
        own, selected, _ = _scope_rows(_catalog(cur), scope, filters)
    if any(filters.get(key) for key in ('uniao', 'associacao', 'escola')) and not selected:
        raise ValueError('O filtro selecionado está fora do seu acesso.')
    return own, selected


def get_export_options(user_id):
    own, selected = _authorized_schools(user_id, {})
    names = [row['escola'].strip().lower() for row in selected]
    with get_db_cursor(commit=False) as cur:
        cur.execute('''SELECT DISTINCT ano, bimestre FROM (
            SELECT ano, bimestre FROM pluraal.aluno WHERE LOWER(TRIM(escola)) = ANY(%s)
            UNION
            SELECT ano, bimestre FROM pluraal.gabarito_aluno WHERE LOWER(TRIM(escola)) = ANY(%s)
        ) periods''', (names, names))
        periods = cur.fetchall()
    return {
        'entidades': own,
        'anos': sorted({r['ano'] for r in periods if r['ano']}, reverse=True),
        'bimestres': sorted({r['bimestre'] for r in periods if r['bimestre']}),
    }


def prepare_export(user_id, table, filters):
    if table not in TABLES:
        raise ValueError('Tabela inválida para exportação.')
    _, selected = _authorized_schools(user_id, filters)
    names = [row['escola'].strip().lower() for row in selected]
    clauses = ['LOWER(TRIM(escola)) = ANY(%s)']
    values = [names]
    for field in ('ano', 'bimestre'):
        if filters.get(field):
            clauses.append(f'{field} = %s')
            values.append(filters[field])
    query = f'SELECT * FROM pluraal.{table} WHERE ' + ' AND '.join(clauses)
    filename = f'pluraal_{table}_{date.today().isoformat()}.csv'
    return filename, _csv_rows(query, values)


def _csv_rows(query, values):
    # A server-side cursor keeps large exports from filling application memory.
    with get_db_connection() as conn:
        with conn.cursor(name='pluraal_export') as cur:
            cur.execute(query, values)
            buffer = io.StringIO()
            writer = csv.writer(buffer, delimiter=';')
            writer.writerow([column.name for column in cur.description])
            yield '\ufeff' + buffer.getvalue()
            while rows := cur.fetchmany(1000):
                buffer = io.StringIO()
                writer = csv.writer(buffer, delimiter=';')
                for row in rows:
                    # Keep spreadsheet programs from evaluating database text as formulas.
                    writer.writerow(["'" + value if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')) else value
                                     for value in row.values()])
                yield buffer.getvalue()
