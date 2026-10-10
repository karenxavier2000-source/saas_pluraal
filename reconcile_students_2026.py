"""Make MySQL 2026 student facts mirror pluraal.aluno without schema changes.

2025 rows remain untouched. Dry run unless --apply is supplied.
"""

import argparse
from datetime import datetime, time
from decimal import Decimal
import os

import mysql.connector
import psycopg
from dotenv import load_dotenv


def as_datetime(day, hour):
    if day is None:
        return None
    return datetime.combine(day, hour or time.min)


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
        pc = pg.cursor()
        mc = my.cursor()
        pc.execute("SELECT count(*) FROM pluraal.aluno WHERE ano='2026'")
        expected = pc.fetchone()[0]
        mc.execute('''SELECT count(*),count(DISTINCT PG_SOURCE_ID),
            sum(PG_SOURCE_ID IS NULL) FROM alunos_simulados WHERE ANO=2026''')
        total, linked, extra = mc.fetchone()
        mc.execute('SELECT count(*) FROM alunos_simulados WHERE ANO=2025')
        historical = mc.fetchone()[0]
        print(f'PostgreSQL 2026: {expected}; MySQL vinculados: {linked}; '
              f'MySQL extras: {extra}; 2025 preservados: {historical}', flush=True)
        if linked != expected:
            raise ValueError('A contagem de PG_SOURCE_ID não corresponde à fonte')
        if not args.apply:
            print('Prévia concluída; nenhum dado alterado.')
            return

        mc.execute('''CREATE TEMPORARY TABLE tmp_aluno_pg (
            pg_id CHAR(36) PRIMARY KEY,
            id_simulado TEXT, escola TEXT, data_inicio DATETIME,
            data_fim DATETIME, ano INT, nome_simulado TEXT,
            serie TEXT, nivel TEXT, nivel_serie TEXT, tipo_simulado TEXT,
            disciplina TEXT, bimestre TEXT, participante TEXT, turma TEXT,
            total_questao INT, desempenho DECIMAL(10,4), materia TEXT,
            total_acertos INT, ra TEXT, total_final DECIMAL(10,4),
            data_insercao DATETIME
        )''')
        insert_sql = '''INSERT INTO tmp_aluno_pg
            (pg_id,id_simulado,escola,data_inicio,data_fim,ano,
             nome_simulado,serie,nivel,nivel_serie,tipo_simulado,
             disciplina,bimestre,participante,turma,total_questao,
             desempenho,materia,total_acertos,ra,total_final,data_insercao)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s)'''
        # A named cursor streams rows instead of loading the whole source.
        source = pg.cursor(name='student_reconcile_stream')
        source.execute('''SELECT id,id_simulado,escola,inicio,hora_inicio,
            fim,hora_fim,ano,nome_simulado,serie,nivel,nivel_serie,
            tipo_simulado,disciplina,bimestre,alunos,turma,
            total_questao,qtd_questao_disciplina,nota_disciplina,
            materia_simulado,qtd_acertos_disciplina,ra,total_final,
            data_ultima_insercao
            FROM pluraal.aluno WHERE ano='2026' ORDER BY id''')
        staged = 0
        while rows := source.fetchmany(2000):
            batch = []
            for row in rows:
                (id_, exam, school, start_day, start_hour, end_day, end_hour,
                 year, title, series, level, level_series, exam_type, subject,
                 bimester, student, classroom, total_questions,
                 subject_questions, score, subject_group, correct,
                 ra, final_score, inserted_at) = row
                performance = score / Decimal(100) if score is not None else None
                batch.append((str(id_), exam, school,
                    as_datetime(start_day, start_hour),
                    as_datetime(end_day, end_hour), int(year), title,
                    series, level, level_series, exam_type, subject,
                    bimester, student, classroom,
                    total_questions if total_questions is not None else subject_questions,
                    performance, subject_group, correct, ra, final_score,
                    inserted_at))
            mc.executemany(insert_sql, batch)
            staged += len(batch)
            if staged % 50000 < len(batch):
                print(f'Fonte preparada: {staged}', flush=True)
        source.close()
        if staged != expected:
            raise ValueError(f'Fonte preparada incompleta: {staged}/{expected}')
        # Verify every source ID exists before replacing any target values.
        mc.execute('''SELECT count(*) FROM tmp_aluno_pg p
            LEFT JOIN alunos_simulados a ON a.PG_SOURCE_ID=p.pg_id
            WHERE a.id IS NULL''')
        missing = mc.fetchone()[0]
        if missing:
            raise ValueError(f'{missing} IDs de origem não existem no MySQL')

        mc.execute('''UPDATE alunos_simulados a
            JOIN tmp_aluno_pg p ON a.PG_SOURCE_ID=p.pg_id
            SET a.ID_SIMULADO=p.id_simulado,
                a.ESCOLA=p.escola,
                a.DATA_INICIO=p.data_inicio,
                a.DATA_FIM=p.data_fim,
                a.ANO=p.ano,
                a.NOME_COMPLETO_SIMULADO=p.nome_simulado,
                a.SERIE=p.serie,
                a.NIVEL=p.nivel,
                a.NIVEL_SERIE=p.nivel_serie,
                a.TIPO_SIMULADO=p.tipo_simulado,
                a.DISCIPLINA=p.disciplina,
                a.BIMESTRE=p.bimestre,
                a.PARTICIPANTE=p.participante,
                a.TURMA=p.turma,
                a.TOTAL_QUESTAO_SIMULADO=p.total_questao,
                a.DESEMPENHO=p.desempenho,
                a.MATERIA=p.materia,
                a.TOTAL_ACERTOS=p.total_acertos,
                a.RA=p.ra,
                a.TOTAL_FINAL=p.total_final,
                a.data_insercao=p.data_insercao
            WHERE a.ANO=2026''')
        print(f'Linhas atualizadas: {mc.rowcount}', flush=True)
        mc.execute('DELETE FROM alunos_simulados WHERE ANO=2026 AND PG_SOURCE_ID IS NULL')
        removed = mc.rowcount
        if removed != extra:
            raise ValueError(f'Extras removidos: {removed}/{extra}')
        mc.execute('''SELECT count(*),count(DISTINCT PG_SOURCE_ID)
            FROM alunos_simulados WHERE ANO=2026''')
        count, distinct_ids = mc.fetchone()
        mc.execute('SELECT count(*) FROM alunos_simulados WHERE ANO=2025')
        historical_after = mc.fetchone()[0]
        if (count, distinct_ids, historical_after) != (expected, expected, historical):
            raise ValueError('A validação de contagens falhou')
        my.commit()
        print(f'Concluído: {count} linhas de 2026; {removed} extras removidos; '
              f'{historical_after} linhas de 2025 preservadas.', flush=True)
    except Exception:
        my.rollback()
        raise
    finally:
        pg.close()
        my.close()


if __name__ == '__main__':
    main()
