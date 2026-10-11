"""Link the nine 2026 source-school names to the school catalogs.

Run without --apply to preview. With --apply, updates PostgreSQL and MySQL.
Existing legacy school names remain available for historical PAAEB data.
"""

import argparse
import os

import mysql.connector
import psycopg
from dotenv import load_dotenv


# Source name, existing PostgreSQL catalog ID (when only spelling differs),
# union code/name, association code/name.
SCHOOLS = [
    ("IAPE - Instituto Adventista Pernambucano de Ensino", None,
     "UNEB", "União Nordeste Brasileira", "UNEB", "União Nordeste Brasileira"),
    ("Colégio Adventista de Natal", None,
     "UNEB", "União Nordeste Brasileira", "MPR", "Missão Rio Grande do Norte - Paraíba"),
    ("Colégio Adventista Boa Vista - PR", 614066,
     "USB", "União Sul Brasileira", "ACP", "Associação Central Paranaense"),
    ("Escola Adventista de Boa Vista - RR", 540851,
     "UNOB", "União Noroeste Brasileira", "AAMAR", "Associação Amazonas Roraima"),
    ("IAAMO - Instituto Adventista da Amazônia Ocidental", 299045,
     "UNOB", "União Noroeste Brasileira", "UNOB", "União Noroeste Brasileira"),
    ("Colégio Adventista Centro América", None,
     "UCOB", "União Centro Oeste Brasileira", "ALM", "Associação Leste Mato-Grossense"),
    ("Colégio Adventista de Pedreira - APSe", None,
     "UCB", "União Central Brasileira", "APSE", "Associação Paulista Sudeste"),
    ("Colégio UNIAENE", None,
     "ULB", "União Leste Brasileira", "ULB", "União Leste Brasileira"),
    ("Colégio Adventista Amazonas - Campus Residencial - IAAI", 285724,
     "UNOB", "União Noroeste Brasileira", "UNOB", "União Noroeste Brasileira"),
]


def update_postgres(conn):
    with conn.cursor() as cur:
        for name, existing_id, union_code, union_name, assoc_code, assoc_name in SCHOOLS:
            cur.execute('SELECT DISTINCT escola FROM pluraal.aluno WHERE escola = %s', (name,))
            if cur.fetchone() is None:
                raise ValueError(f"Nome ausente na fonte PostgreSQL: {name}")
            cur.execute('SELECT id_escolas FROM pluraal.escolas_pluraal WHERE "ESCOLA" = %s', (name,))
            exact = [row[0] for row in cur.fetchall()]
            if len(exact) > 1:
                raise ValueError(f"Nome duplicado no catálogo PostgreSQL: {name}")
            if exact:
                target_id = exact[0]
            elif existing_id is not None:
                cur.execute('SELECT id_escolas FROM pluraal.escolas_pluraal WHERE id_escolas = %s', (existing_id,))
                if cur.fetchone() is None:
                    raise ValueError(f"ID esperado ausente no PostgreSQL: {existing_id}")
                target_id = existing_id
            else:
                cur.execute('''INSERT INTO pluraal.escolas_pluraal
                    ("UNIAO", "SIGLA_UNIAO", "ASSOCIACAO", "SIGLA_ASSOCIACAO", "ESCOLA")
                    VALUES (%s, %s, %s, %s, %s) RETURNING id_escolas''',
                    (union_name, union_code, assoc_name, assoc_code, name))
                target_id = cur.fetchone()[0]
            cur.execute('''UPDATE pluraal.escolas_pluraal SET
                "ESCOLA"=%s, "UNIAO"=%s, "SIGLA_UNIAO"=%s,
                "ASSOCIACAO"=%s, "SIGLA_ASSOCIACAO"=%s
                WHERE id_escolas=%s''',
                (name, union_name, union_code, assoc_name, assoc_code, target_id))
            print(f"PostgreSQL: {target_id} -> {name} ({union_code}/{assoc_code})")


def update_mysql(conn):
    cur = conn.cursor()
    try:
        for name, _, union_code, union_name, assoc_code, assoc_name in SCHOOLS:
            # BINARY makes the check exact under MySQL's case/accent-insensitive collation.
            cur.execute('SELECT id_escolas FROM escolas_pluraal WHERE BINARY ESCOLA = BINARY %s', (name,))
            exact = [row[0] for row in cur.fetchall()]
            if len(exact) > 1:
                raise ValueError(f"Nome duplicado no catálogo MySQL: {name}")
            if exact:
                target_id = exact[0]
            else:
                cur.execute('SELECT id_escolas, ESCOLA FROM escolas_pluraal WHERE SIGLA_UNIAO=%s AND SIGLA_ASSOCIACAO=%s',
                            (union_code, assoc_code))
                candidates = cur.fetchall()
                # Only spelling variants can be renamed. Older school names
                # (Natal, Pedreira, Centro América, Bahia) stay as aliases.
                old = {
                    "IAAMO - Instituto Adventista da Amazônia Ocidental": "IAAMO – Instituto Adventista da Amazônia Ocidental",
                }.get(name)
                matches = [row[0] for row in candidates if row[1] == old] if old else []
                if len(matches) == 1:
                    target_id = matches[0]
                else:
                    cur.execute('''INSERT INTO escolas_pluraal
                        (UNIAO, SIGLA_UNIAO, ASSOCIACAO, SIGLA_ASSOCIACAO, ESCOLA)
                        VALUES (%s,%s,%s,%s,%s)''',
                        (union_name, union_code, assoc_name, assoc_code, name))
                    target_id = cur.lastrowid
            cur.execute('''UPDATE escolas_pluraal SET ESCOLA=%s, UNIAO=%s,
                SIGLA_UNIAO=%s, ASSOCIACAO=%s, SIGLA_ASSOCIACAO=%s
                WHERE id_escolas=%s''',
                (name, union_name, union_code, assoc_name, assoc_code, target_id))
            print(f"MySQL: {target_id} -> {name} ({union_code}/{assoc_code})")
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
        update_postgres(pg)
        update_mysql(my)
        if args.apply:
            pg.commit()
            my.commit()
            print('Alterações gravadas nos dois bancos.')
        else:
            pg.rollback()
            my.rollback()
            print('Prévia concluída; transações revertidas.')
    except Exception:
        pg.rollback()
        my.rollback()
        raise
    finally:
        pg.close()
        my.close()


if __name__ == '__main__':
    main()
