"""Consolidate the short IAAI school alias into its canonical campus name.

Preview by default. --apply merges duplicate facts, renames unique facts,
and removes the obsolete catalog entry from PostgreSQL and MySQL.
"""

import argparse
import os
from collections import Counter

import mysql.connector
import psycopg
from dotenv import load_dotenv


OLD = 'Colégio Adventista Amazonas - IAAI'
NEW = 'Colégio Adventista Amazonas - Campus Residencial - IAAI'
CASE_VARIANT = 'Colégio Adventista Amazonas - Campus Residencial - Iaai'
ALIASES = (OLD, CASE_VARIANT)
OLD_PG_ID = 167169
NEW_PG_ID = 285724
OLD_MY_ID = 110
NEW_MY_ID = 109
TABLE_KEYS = {
    'alunos_simulados': ('ID_SIMULADO', 'ANO', 'PARTICIPANTE', 'DISCIPLINA'),
    'mapa_simulados': ('ID_SIMULADO', 'ANO', 'ID_QUESTAO'),
    'questao_simulado': ('ID_SIMULADO', 'ANO', 'ID_QUESTAO'),
    'simulados': ('id_simulado',),
}


def mysql_rows(cur, table):
    school_col = 'escola' if table == 'simulados' else 'ESCOLA'
    cur.execute(f'''SELECT * FROM `{table}`
        WHERE BINARY `{school_col}` = BINARY %s
           OR BINARY `{school_col}` = BINARY %s
           OR BINARY `{school_col}` = BINARY %s''', (OLD, CASE_VARIANT, NEW))
    rows = cur.fetchall()
    return school_col, [r for r in rows if r[school_col] in ALIASES], [r for r in rows if r[school_col] == NEW]


def merge_table(cur, table, key_columns, apply):
    school_col, alias_rows, new_rows = mysql_rows(cur, table)
    def key(row):
        return tuple(row[col] for col in key_columns)

    if any(count > 1 for count in Counter(key(r) for r in new_rows).values()):
        raise ValueError(f'Chave natural duplicada no nome correto em {table}')
    # Exact canonical spelling wins; among aliases the full campus name wins.
    survivors = {key(r): r for r in new_rows}
    duplicates = []
    for row in sorted(alias_rows, key=lambda r: 0 if r[school_col] == CASE_VARIANT else 1):
        existing = survivors.get(key(row))
        if existing is None:
            survivors[key(row)] = row
        else:
            duplicates.append((row, existing))
    unique = len(alias_rows) - len(duplicates)
    print(f'{table}: {len(alias_rows)} variantes; {len(duplicates)} repetidos; {unique} exclusivos')
    if not apply:
        return

    for old_row, current in duplicates:
        # Keep the canonical row's recorded values when both are populated.
        # Fill only empty fields from the legacy row before removing it.
        changes = {col: value for col, value in old_row.items()
                   if col not in ('id', school_col, 'data_insercao', 'PG_SOURCE_ID')
                   and col not in key_columns
                   and current[col] in (None, '') and value not in (None, '')}
        if changes:
            assignments = ', '.join(f'`{col}`=%s' for col in changes)
            cur.execute(f'UPDATE `{table}` SET {assignments} WHERE id=%s',
                        (*changes.values(), current['id']))
            current.update(changes)
    ids = [r['id'] for r, _ in duplicates]
    for start in range(0, len(ids), 500):
        batch = ids[start:start + 500]
        cur.execute(f'DELETE FROM `{table}` WHERE id IN ({",".join(["%s"] * len(batch))})', batch)
    cur.execute(f'''UPDATE `{table}` SET `{school_col}`=%s
        WHERE BINARY `{school_col}`=BINARY %s
           OR BINARY `{school_col}`=BINARY %s''', (NEW, OLD, CASE_VARIANT))
    if cur.rowcount != unique:
        raise ValueError(f'Quantidade migrada inesperada em {table}: {cur.rowcount} != {unique}')


def check_catalogs(pg, my):
    with pg.cursor() as cur:
        cur.execute('''SELECT id_escolas, "ESCOLA" FROM pluraal.escolas_pluraal
            WHERE id_escolas IN (%s,%s)''', (OLD_PG_ID, NEW_PG_ID))
        if sorted(cur.fetchall()) != sorted([(OLD_PG_ID, OLD), (NEW_PG_ID, NEW)]):
            raise ValueError('Catálogo PostgreSQL inesperado')
        cur.execute('SELECT count(*) FROM pluraal.usuario_acesso WHERE id_escolas=%s', (OLD_PG_ID,))
        if cur.fetchone()[0]:
            raise ValueError('Há acesso de usuário vinculado ao ID antigo no PostgreSQL')
    cur = my.cursor()
    try:
        cur.execute('SELECT id_escolas,ESCOLA FROM escolas_pluraal WHERE id_escolas IN (%s,%s)',
                    (OLD_MY_ID, NEW_MY_ID))
        if sorted(cur.fetchall()) != sorted([(OLD_MY_ID, OLD), (NEW_MY_ID, NEW)]):
            raise ValueError('Catálogo MySQL inesperado')
    finally:
        cur.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    load_dotenv('.env')
    pg = psycopg.connect(host=os.getenv('PGHOST'), port=os.getenv('PGPORT'),
                        dbname=os.getenv('PGDATABASE'), user=os.getenv('PGUSER'),
                        password=os.getenv('PGPASSWORD'))
    my = mysql.connector.connect(host=os.getenv('MYSQL_HOST'),
                                 port=int(os.getenv('MYSQL_PORT', '3306')),
                                 database=os.getenv('MYSQL_DB'),
                                 user=os.getenv('MYSQL_USER'),
                                 password=os.getenv('MYSQL_PASSWORD'), autocommit=False)
    try:
        check_catalogs(pg, my)
        cur = my.cursor(dictionary=True)
        try:
            for table, keys in TABLE_KEYS.items():
                merge_table(cur, table, keys, args.apply)
            if args.apply:
                cur.execute('DELETE FROM escolas_pluraal WHERE id_escolas=%s AND BINARY ESCOLA=BINARY %s',
                            (OLD_MY_ID, OLD))
                if cur.rowcount != 1:
                    raise ValueError('Cadastro MySQL antigo não foi excluído')
                with pg.cursor() as pg_cur:
                    pg_cur.execute('DELETE FROM pluraal.escolas_pluraal WHERE id_escolas=%s AND "ESCOLA"=%s',
                                   (OLD_PG_ID, OLD))
                    if pg_cur.rowcount != 1:
                        raise ValueError('Cadastro PostgreSQL antigo não foi excluído')
                for table in TABLE_KEYS:
                    col = 'escola' if table == 'simulados' else 'ESCOLA'
                    cur.execute(f'''SELECT count(*) AS n FROM `{table}`
                        WHERE BINARY `{col}`=BINARY %s OR BINARY `{col}`=BINARY %s''', ALIASES)
                    if cur.fetchone()['n']:
                        raise ValueError(f'Nome antigo ainda encontrado em {table}')
                my.commit()
                pg.commit()
                print('Consolidação gravada nos dois bancos.')
            else:
                print('Prévia concluída; nenhum dado alterado.')
        finally:
            cur.close()
    except Exception:
        my.rollback()
        pg.rollback()
        raise
    finally:
        my.close()
        pg.close()


if __name__ == '__main__':
    main()
