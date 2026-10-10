"""Synchronize unambiguous 2026 educational catalog data from PostgreSQL to MySQL.

Dry run by default. Existing nonempty MySQL values are never overwritten.
"""

import argparse
from datetime import datetime, time
import os
import re
import unicodedata

import mysql.connector
from dotenv import load_dotenv

from Backend.database.connection import get_db_cursor
from Backend.services.report_service import _student_identity


def canonical(value):
    clean = ' '.join(str(value or '').strip().casefold().split())
    return ''.join(char for char in unicodedata.normalize('NFKD', clean)
                   if not unicodedata.combining(char))


def mysql_connection():
    load_dotenv('.env')
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DB'),
        autocommit=False,
    )


def read_source():
    with get_db_cursor(commit=False) as cur:
        cur.execute('''SELECT "ESCOLA" escola, "UNIAO" uniao,
                       "SIGLA_UNIAO" sigla_uniao, "ASSOCIACAO" associacao,
                       "SIGLA_ASSOCIACAO" sigla_associacao
                FROM pluraal.escolas_pluraal''')
        schools = cur.fetchall()
        cur.execute(f'''WITH attempts AS (
            SELECT LOWER(TRIM(a.escola)) escola, a.id_simulado,
                   {_student_identity('a')} aluno,
                   MAX(a.nome_simulado) descricao,
                   MAX(a.total_final) nota,
                   MAX(a.total_questao) questoes
            FROM pluraal.aluno a
            WHERE a.ano = '2026' AND a.id_simulado IS NOT NULL
            GROUP BY 1, 2, 3
        )
        SELECT escola, id_simulado, MAX(descricao) descricao,
               COUNT(*) esperados,
               COUNT(*) FILTER (WHERE nota IS NOT NULL AND questoes > 0) participantes
        FROM attempts GROUP BY 1, 2''')
        exams = cur.fetchall()
    return schools, exams


def sync_catalog(cur, schools, apply):
    cur.execute('''SELECT id_escolas, ESCOLA, UNIAO, SIGLA_UNIAO,
                          ASSOCIACAO, SIGLA_ASSOCIACAO FROM escolas_pluraal''')
    existing = {canonical(row['ESCOLA']): row for row in cur.fetchall()}
    inserts = []
    updates = []
    for source in schools:
        name = canonical(source['escola'])
        if not name:
            continue
        values = (source['uniao'], source['sigla_uniao'],
                  source['associacao'], source['sigla_associacao'])
        target = existing.get(name)
        if target is None:
            inserts.append((*values, source['escola']))
        else:
            changes = [value if not target[column] else None for column, value in zip(
                ('UNIAO', 'SIGLA_UNIAO', 'ASSOCIACAO', 'SIGLA_ASSOCIACAO'), values)]
            if any(value is not None for value in changes):
                updates.append((*changes, target['id_escolas']))
    if apply:
        if inserts:
            cur.executemany('''INSERT INTO escolas_pluraal
                (UNIAO, SIGLA_UNIAO, ASSOCIACAO, SIGLA_ASSOCIACAO, ESCOLA)
                VALUES (%s,%s,%s,%s,%s)''', inserts)
        if updates:
            cur.executemany('''UPDATE escolas_pluraal SET
                UNIAO=COALESCE(NULLIF(UNIAO,''),%s),
                SIGLA_UNIAO=COALESCE(NULLIF(SIGLA_UNIAO,''),%s),
                ASSOCIACAO=COALESCE(NULLIF(ASSOCIACAO,''),%s),
                SIGLA_ASSOCIACAO=COALESCE(NULLIF(SIGLA_ASSOCIACAO,''),%s)
                WHERE id_escolas=%s''', updates)
    return len(inserts), len(updates)


def sync_exams(cur, exams, school_names, apply):
    cur.execute('''SELECT id, id_simulado, escola, descricao, ano,
                          Qtd_participantes_esperado esperados,
                          Qtd_participantes participantes FROM simulados''')
    existing = {(canonical(row['id_simulado']), canonical(row['escola'])): row
                for row in cur.fetchall()}
    inserts = []
    updates = []
    for source in exams:
        key = (canonical(source['id_simulado']), canonical(source['escola']))
        if not all(key):
            continue
        target = existing.get(key)
        school_name = school_names.get(key[1], source['escola'])
        if target is None:
            inserts.append((source['id_simulado'], source['descricao'], 2026,
                            school_name, source['esperados'], source['participantes']))
        elif any(target[column] is None or target[column] == '' for column in
                 ('descricao', 'ano', 'esperados', 'participantes')):
            updates.append((source['descricao'], 2026, source['esperados'],
                            source['participantes'], target['id']))
    if apply:
        if inserts:
            cur.executemany('''INSERT INTO simulados
                (id_simulado, descricao, ano, escola,
                 Qtd_participantes_esperado, Qtd_participantes)
                VALUES (%s,%s,%s,%s,%s,%s)''', inserts)
        if updates:
            cur.executemany('''UPDATE simulados SET
                descricao=COALESCE(NULLIF(descricao,''),%s),
                ano=COALESCE(ano,%s),
                Qtd_participantes_esperado=COALESCE(Qtd_participantes_esperado,%s),
                Qtd_participantes=COALESCE(Qtd_participantes,%s)
                WHERE id=%s''', updates)
    return len(inserts), len(updates)


def datetime_value(day, hour):
    if day is None:
        return None
    return datetime.combine(day, hour or time.min)


def ensure_student_columns(cur, apply):
    cur.execute('SHOW COLUMNS FROM alunos_simulados')
    columns = {row['Field'] for row in cur.fetchall()}
    missing = {'PG_SOURCE_ID', 'TOTAL_FINAL', 'RA'} - columns
    if not apply:
        return missing
    definitions = {
        'PG_SOURCE_ID': 'CHAR(36) NULL',
        'TOTAL_FINAL': 'DECIMAL(10,4) NULL',
        'RA': 'TEXT NULL',
    }
    for column in sorted(missing):
        cur.execute(f'ALTER TABLE alunos_simulados ADD COLUMN {column} {definitions[column]}')
    cur.execute('SHOW INDEX FROM alunos_simulados WHERE Key_name=%s', ('uq_pg_source_id',))
    if not cur.fetchone():
        cur.execute('ALTER TABLE alunos_simulados ADD UNIQUE KEY uq_pg_source_id (PG_SOURCE_ID)')
    return missing


def sync_students(cur, school_names, apply):
    missing_columns = ensure_student_columns(cur, apply)
    select_pg_id = 'PG_SOURCE_ID' if 'PG_SOURCE_ID' not in missing_columns or apply else 'NULL PG_SOURCE_ID'
    cur.execute(f'''SELECT id, ID_SIMULADO, ESCOLA, PARTICIPANTE,
                           DISCIPLINA, {select_pg_id}
                    FROM alunos_simulados WHERE ANO=2026''')
    targets = {}
    source_ids = set()
    for row in cur:
        key = tuple(canonical(row[field]) for field in
                    ('ESCOLA', 'ID_SIMULADO', 'PARTICIPANTE', 'DISCIPLINA'))
        targets.setdefault(key, []).append((row['id'], row['PG_SOURCE_ID']))
        if row['PG_SOURCE_ID']:
            source_ids.add(row['PG_SOURCE_ID'])

    if apply:
        cur.execute('''CREATE TEMPORARY TABLE tmp_student_sync (
            target_id BIGINT PRIMARY KEY, pg_id CHAR(36), ra TEXT,
            total_final DECIMAL(10,4), desempenho DECIMAL(10,4),
            total_acertos INT, total_questao INT,
            data_inicio DATETIME, data_fim DATETIME,
            nome_simulado TEXT, serie TEXT, nivel TEXT,
            nivel_serie TEXT, tipo_simulado TEXT, bimestre TEXT,
            turma TEXT, materia TEXT
        )''')

    update_sql = '''INSERT INTO tmp_student_sync
        (target_id, pg_id, ra, total_final, desempenho, total_acertos,
         total_questao, data_inicio, data_fim, nome_simulado, serie,
         nivel, nivel_serie, tipo_simulado, bimestre, turma, materia)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
    insert_sql = '''INSERT INTO alunos_simulados
        (PG_SOURCE_ID, RA, TOTAL_FINAL, ID_SIMULADO, ESCOLA,
         DATA_INICIO, DATA_FIM, ANO, NOME_COMPLETO_SIMULADO,
         SERIE, NIVEL, NIVEL_SERIE, TIPO_SIMULADO, DISCIPLINA,
         BIMESTRE, PARTICIPANTE, TURMA, TOTAL_QUESTAO_SIMULADO,
         DESEMPENHO, MATERIA, TOTAL_ACERTOS)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
    update_batch, insert_batch = [], []
    updates = inserts = already = 0
    used_target_ids = set()
    with get_db_cursor(commit=False) as pg:
        pg.execute('''SELECT id, escola, id_simulado, alunos, ra,
                    disciplina, inicio, fim, hora_inicio, hora_fim,
                    ano, nome_simulado, serie, nivel, nivel_serie,
                    tipo_simulado, bimestre, turma, total_questao,
                    nota_disciplina, total_final, materia_simulado,
                    qtd_acertos_disciplina
                FROM pluraal.aluno
                WHERE ano='2026' AND id_simulado IS NOT NULL''')
        for row in pg:
            pg_id = str(row['id'])
            if pg_id in source_ids:
                already += 1
                continue
            key = tuple(canonical(row[field]) for field in
                        ('escola', 'id_simulado', 'alunos', 'disciplina'))
            target_id = next((id_ for id_, assigned in targets.get(key, [])
                              if id_ not in used_target_ids and assigned is None), None)
            score = row['nota_disciplina'] / 100 if row['nota_disciplina'] is not None else None
            start = datetime_value(row['inicio'], row['hora_inicio'])
            end = datetime_value(row['fim'], row['hora_fim'])
            if target_id is not None:
                used_target_ids.add(target_id)
                updates += 1
                if apply:
                    update_batch.append((target_id, pg_id, row['ra'], row['total_final'],
                        score, row['qtd_acertos_disciplina'], row['total_questao'],
                        start, end, row['nome_simulado'], row['serie'], row['nivel'],
                        row['nivel_serie'], row['tipo_simulado'], row['bimestre'],
                        row['turma'], row['materia_simulado']))
                    if len(update_batch) >= 2000:
                        cur.executemany(update_sql, update_batch)
                        update_batch.clear()
            else:
                inserts += 1
                if apply:
                    school = school_names.get(canonical(row['escola']), row['escola'])
                    insert_batch.append((pg_id, row['ra'], row['total_final'],
                        row['id_simulado'], school, start, end, 2026,
                        row['nome_simulado'], row['serie'], row['nivel'],
                        row['nivel_serie'], row['tipo_simulado'], row['disciplina'],
                        row['bimestre'], row['alunos'], row['turma'],
                        row['total_questao'], score, row['materia_simulado'],
                        row['qtd_acertos_disciplina']))
                    if len(insert_batch) >= 2000:
                        cur.executemany(insert_sql, insert_batch)
                        insert_batch.clear()
            if apply and (updates + inserts) % 50000 == 0:
                print(f'alunos processados: {updates + inserts}', flush=True)
    if apply:
        if update_batch:
            cur.executemany(update_sql, update_batch)
        if insert_batch:
            cur.executemany(insert_sql, insert_batch)
        cur.execute('''UPDATE alunos_simulados a
            JOIN tmp_student_sync s ON a.id=s.target_id
            SET a.PG_SOURCE_ID=COALESCE(a.PG_SOURCE_ID,s.pg_id),
                a.RA=COALESCE(NULLIF(a.RA,''),s.ra),
                a.TOTAL_FINAL=COALESCE(a.TOTAL_FINAL,s.total_final),
                a.DESEMPENHO=COALESCE(a.DESEMPENHO,s.desempenho),
                a.TOTAL_ACERTOS=COALESCE(a.TOTAL_ACERTOS,s.total_acertos),
                a.TOTAL_QUESTAO_SIMULADO=COALESCE(a.TOTAL_QUESTAO_SIMULADO,s.total_questao),
                a.DATA_INICIO=COALESCE(a.DATA_INICIO,s.data_inicio),
                a.DATA_FIM=COALESCE(a.DATA_FIM,s.data_fim),
                a.NOME_COMPLETO_SIMULADO=COALESCE(NULLIF(a.NOME_COMPLETO_SIMULADO,''),s.nome_simulado),
                a.SERIE=COALESCE(NULLIF(a.SERIE,''),s.serie),
                a.NIVEL=COALESCE(NULLIF(a.NIVEL,''),s.nivel),
                a.NIVEL_SERIE=COALESCE(NULLIF(a.NIVEL_SERIE,''),s.nivel_serie),
                a.TIPO_SIMULADO=COALESCE(NULLIF(a.TIPO_SIMULADO,''),s.tipo_simulado),
                a.BIMESTRE=COALESCE(NULLIF(a.BIMESTRE,''),s.bimestre),
                a.TURMA=COALESCE(NULLIF(a.TURMA,''),s.turma),
                a.MATERIA=COALESCE(NULLIF(a.MATERIA,''),s.materia)''')
    return {'columns_added': sorted(missing_columns), 'matched': updates,
            'inserted': inserts, 'already_synced': already}


def sync_question_skills(cur, apply):
    with get_db_cursor(commit=False) as pg:
        pg.execute('''SELECT id_simulado, id_questao, MAX(habilidade) habilidade
            FROM pluraal.questao_simulados
            WHERE ano='2026' AND NULLIF(TRIM(habilidade),'') IS NOT NULL
            GROUP BY 1, 2''')
        skills = {(canonical(row['id_simulado']), canonical(row['id_questao'])):
                  row['habilidade'] for row in pg}
    result = {}
    for table in ('mapa_simulados', 'questao_simulado'):
        cur.execute(f'''SELECT id, ID_SIMULADO, ESCOLA, ID_QUESTAO
            FROM {table} WHERE ANO=2026
              AND (HABILIDADE IS NULL OR TRIM(HABILIDADE)='')''')
        updates = []
        for row in cur:
            key = (canonical(row['ID_SIMULADO']), canonical(row['ID_QUESTAO']))
            skill = skills.get(key)
            if skill and row['ESCOLA']:
                updates.append((skill, row['id']))
        if apply and updates:
            cur.executemany(f'''UPDATE {table} SET HABILIDADE=%s
                WHERE id=%s AND (HABILIDADE IS NULL OR TRIM(HABILIDADE)='')''', updates)
        result[table] = len(updates)
    return result


def sync_question_map(cur, school_names, apply):
    cur.execute('''SELECT ID_SIMULADO, ESCOLA, ID_QUESTAO
        FROM mapa_simulados WHERE ANO=2026''')
    existing = {tuple(canonical(row[field]) for field in
                      ('ID_SIMULADO', 'ESCOLA', 'ID_QUESTAO')) for row in cur}
    inserts = []
    with get_db_cursor(commit=False) as pg:
        pg.execute('''WITH questions AS (
            SELECT DISTINCT ON (id_simulado, id_questao)
                id_simulado, id_questao, sequencia, enunciado,
                disciplina, habilidade, dificuldade, gabarito,
                data_insercao
            FROM pluraal.questao_simulados
            WHERE ano='2026' AND id_simulado IS NOT NULL
              AND id_questao IS NOT NULL
            ORDER BY id_simulado, id_questao, id
        ), exam_schools AS (
            SELECT DISTINCT id_simulado, LOWER(TRIM(escola)) escola
            FROM pluraal.aluno WHERE ano='2026'
              AND id_simulado IS NOT NULL
        )
        SELECT q.*, s.escola FROM questions q
        JOIN exam_schools s ON q.id_simulado=s.id_simulado''')
        for row in pg:
            key = tuple(canonical(row[field]) for field in
                        ('id_simulado', 'escola', 'id_questao'))
            if not all(key) or key in existing:
                continue
            existing.add(key)
            sequence = str(row['sequencia'] or '').strip()
            label = f'QUESTAO {sequence}' if sequence else None
            school = school_names.get(canonical(row['escola']), row['escola'])
            inserts.append((row['id_simulado'], school, 2026,
                row['id_questao'], label, row['enunciado'],
                row['disciplina'], row['habilidade'], row['dificuldade'],
                row['gabarito'], row['data_insercao']))
    if apply and inserts:
        cur.executemany('''INSERT INTO mapa_simulados
            (ID_SIMULADO, ESCOLA, ANO, ID_QUESTAO, QUESTAO,
             ENUNCIADO, DISCIPLINA, HABILIDADE, DIFICULDADE,
             GABARITO, data_insercao)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', inserts)
    return len(inserts)


def sync_question_details(cur, school_names, apply):
    cur.execute('''SELECT ID_SIMULADO, ESCOLA, ID_QUESTAO
        FROM questao_simulado WHERE ANO=2026''')
    existing = {tuple(canonical(row[field]) for field in
                      ('ID_SIMULADO', 'ESCOLA', 'ID_QUESTAO')) for row in cur}
    inserts = []
    with get_db_cursor(commit=False) as pg:
        pg.execute('''WITH questions AS (
            SELECT DISTINCT ON (id_simulado, id_questao)
                id_simulado, id_questao, sequencia, enunciado,
                disciplina, habilidade, dificuldade, data_insercao
            FROM pluraal.questao_simulados
            WHERE ano='2026' AND id_simulado IS NOT NULL
              AND id_questao IS NOT NULL
            ORDER BY id_simulado, id_questao, id
        ), exam_schools AS (
            SELECT id_simulado, LOWER(TRIM(escola)) escola,
                CASE WHEN COUNT(DISTINCT serie)=1 THEN MAX(serie) END serie,
                CASE WHEN COUNT(DISTINCT nivel)=1 THEN MAX(nivel) END nivel,
                CASE WHEN COUNT(DISTINCT nivel_serie)=1 THEN MAX(nivel_serie) END nivel_serie
            FROM pluraal.aluno WHERE ano='2026'
              AND id_simulado IS NOT NULL
            GROUP BY 1, 2
        )
        SELECT q.*, s.escola, s.serie, s.nivel, s.nivel_serie
        FROM questions q JOIN exam_schools s ON q.id_simulado=s.id_simulado''')
        for row in pg:
            key = tuple(canonical(row[field]) for field in
                        ('id_simulado', 'escola', 'id_questao'))
            if not all(key) or key in existing:
                continue
            existing.add(key)
            sequence = str(row['sequencia'] or '').strip()
            label = f'QUESTAO {sequence}' if sequence else None
            school = school_names.get(canonical(row['escola']), row['escola'])
            inserts.append((row['id_simulado'], school, 2026,
                row['serie'], row['nivel'], row['nivel_serie'],
                row['id_questao'], label, row['enunciado'],
                row['disciplina'], row['habilidade'], row['dificuldade'],
                row['data_insercao']))
    if apply and inserts:
        cur.executemany('''INSERT INTO questao_simulado
            (ID_SIMULADO, ESCOLA, ANO, SERIE, NIVEL, NIVEL_SERIE,
             ID_QUESTAO, QUESTAO, ENUNCIADO, DISCIPLINA,
             HABILIDADE, DIFICULDADE, data_insercao)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', inserts)
    return len(inserts)


def question_number(value):
    match = re.search(r'\d+', str(value or ''))
    return str(int(match.group())) if match else None


def sync_answer_counts(cur, apply):
    with get_db_cursor(commit=False) as pg:
        pg.execute('''SELECT id_simulado, id_questao, MIN(sequencia) sequencia
            FROM pluraal.questao_simulados WHERE ano='2026'
            GROUP BY 1, 2''')
        question_sequences = {
            (canonical(row['id_simulado']), canonical(row['id_questao'])):
            question_number(row['sequencia']) for row in pg}
        pg.execute('''SELECT LOWER(TRIM(escola)) escola, id_simulado,
            SUBSTRING(questao FROM '[0-9]+') sequencia,
            COUNT(*) FILTER (WHERE status_questao='ACERTO') acertos,
            COUNT(*) FILTER (WHERE status_questao IN ('ACERTO','ERRO')) avaliadas,
            COUNT(*) FILTER (WHERE UPPER(TRIM(resposta))='A') a,
            COUNT(*) FILTER (WHERE UPPER(TRIM(resposta))='B') b,
            COUNT(*) FILTER (WHERE UPPER(TRIM(resposta))='C') c,
            COUNT(*) FILTER (WHERE UPPER(TRIM(resposta))='D') d,
            COUNT(*) FILTER (WHERE UPPER(TRIM(resposta))='E') e
            FROM pluraal.gabarito_aluno
            WHERE ano='2026' AND questao ~ '[0-9]+'
            GROUP BY 1, 2, 3''')
        answers = {(canonical(row['escola']), canonical(row['id_simulado']),
                    question_number(row['sequencia'])): row for row in pg}
    cur.execute('''SELECT id, ID_SIMULADO, ESCOLA, ID_QUESTAO, QUESTAO,
                          ACERTOS, A, B, C, D, E
        FROM questao_simulado WHERE ANO=2026
          AND (ACERTOS IS NULL OR A IS NULL OR B IS NULL
               OR C IS NULL OR D IS NULL OR E IS NULL)''')
    updates = []
    for row in cur:
        simulado = canonical(row['ID_SIMULADO'])
        sequence = question_number(row['QUESTAO'])
        if not sequence or question_sequences.get(
                (simulado, canonical(row['ID_QUESTAO']))) != sequence:
            continue
        source = answers.get((canonical(row['ESCOLA']), simulado, sequence))
        if not source:
            continue
        score = (source['acertos'] / source['avaliadas']
                 if source['avaliadas'] else None)
        values = [score if row['ACERTOS'] is None else None]
        values.extend(source[letter.lower()] if row[letter] is None
                      and source[letter.lower()] > 0 else None
                      for letter in 'ABCDE')
        if any(value is not None for value in values):
            updates.append((*values, row['id']))
    if apply and updates:
        cur.executemany('''UPDATE questao_simulado SET
            ACERTOS=COALESCE(ACERTOS,%s), A=COALESCE(A,%s),
            B=COALESCE(B,%s), C=COALESCE(C,%s),
            D=COALESCE(D,%s), E=COALESCE(E,%s)
            WHERE id=%s''', updates)
    return len(updates)


def sync_student_question_totals(cur, apply):
    cur.execute('''SELECT PG_SOURCE_ID FROM alunos_simulados
        WHERE ANO=2026 AND PG_SOURCE_ID IS NOT NULL
          AND TOTAL_QUESTAO_SIMULADO IS NULL''')
    missing_ids = {row['PG_SOURCE_ID'] for row in cur}
    updates = []
    with get_db_cursor(commit=False) as pg:
        pg.execute('''SELECT id, qtd_questao_disciplina
            FROM pluraal.aluno WHERE ano='2026'
              AND qtd_questao_disciplina IS NOT NULL''')
        for row in pg:
            if str(row['id']) in missing_ids:
                updates.append((row['qtd_questao_disciplina'], str(row['id'])))
    if apply and updates:
        cur.execute('''CREATE TEMPORARY TABLE tmp_question_totals (
            total INT, pg_id CHAR(36) PRIMARY KEY)''')
        cur.executemany('''INSERT INTO tmp_question_totals (total,pg_id)
            VALUES (%s,%s)''', updates)
        cur.execute('''UPDATE alunos_simulados a
            JOIN tmp_question_totals s ON a.PG_SOURCE_ID=s.pg_id
            SET a.TOTAL_QUESTAO_SIMULADO=s.total
            WHERE a.TOTAL_QUESTAO_SIMULADO IS NULL''')
    return len(updates)


def sync_exam_periods(cur, apply):
    cur.execute('''SELECT id, ID_SIMULADO, ESCOLA FROM alunos_simulados
        WHERE ANO=2026 AND (BIMESTRE IS NULL OR TRIM(BIMESTRE)='')''')
    blanks = list(cur)
    with get_db_cursor(commit=False) as pg:
        pg.execute('''SELECT id_simulado, LOWER(TRIM(escola)) escola,
            CASE WHEN COUNT(DISTINCT bimestre)=1 THEN MAX(bimestre) END bimestre
            FROM pluraal.aluno WHERE ano='2026'
            GROUP BY 1, 2''')
        periods = {(canonical(row['id_simulado']), canonical(row['escola'])):
                   row['bimestre'] for row in pg}
    updates = [(periods[(canonical(row['ID_SIMULADO']), canonical(row['ESCOLA']))], row['id'])
               for row in blanks
               if periods.get((canonical(row['ID_SIMULADO']), canonical(row['ESCOLA'])))]
    if apply and updates:
        cur.executemany('''UPDATE alunos_simulados SET BIMESTRE=%s
            WHERE id=%s AND (BIMESTRE IS NULL OR TRIM(BIMESTRE)='')''', updates)
    return len(updates)


def sync_student_answer_totals(cur, apply):
    cur.execute('''SELECT id, ESCOLA, ID_SIMULADO, RA, PARTICIPANTE,
                          DISCIPLINA, TOTAL_QUESTAO_SIMULADO total_questoes,
                          TOTAL_QUESTAO_RESPONDIDA respondidas,
                          TOTAL_ACERTOS acertos
        FROM alunos_simulados WHERE ANO=2026 AND PG_SOURCE_ID IS NOT NULL
          AND (TOTAL_QUESTAO_RESPONDIDA IS NULL OR TOTAL_ACERTOS IS NULL)''')
    targets = {}
    for row in cur:
        student = (row['RA'] or '').strip()
        if re.fullmatch(r'[0-9]+\.0+', student):
            student = student.split('.')[0]
        if not student:
            student = 'nome:' + (row['PARTICIPANTE'] or '').strip().lower()
        key = (canonical(row['ESCOLA']), canonical(row['ID_SIMULADO']),
               canonical(student), canonical(row['DISCIPLINA']))
        targets.setdefault(key, []).append(row)

    updates = []
    with get_db_cursor(commit=False) as pg:
        pg.execute(f'''SELECT LOWER(TRIM(g.escola)) escola, g.id_simulado,
            {_student_identity('g')} aluno, g.disciplina,
            COUNT(*) respostas,
            COUNT(*) FILTER (WHERE g.status_questao='ACERTO') acertos
            FROM pluraal.gabarito_aluno g
            WHERE g.ano='2026' AND g.status_questao IN ('ACERTO','ERRO')
            GROUP BY 1,2,3,4''')
        for source in pg:
            key = (canonical(source['escola']), canonical(source['id_simulado']),
                   canonical(source['aluno']), canonical(source['disciplina']))
            for target in targets.get(key, []):
                if target['total_questoes'] is not None and source['respostas'] > target['total_questoes']:
                    continue
                respostas = source['respostas'] if target['respondidas'] is None else None
                acertos = source['acertos'] if target['acertos'] is None else None
                if respostas is not None or acertos is not None:
                    updates.append((respostas, acertos, target['id']))
    if apply and updates:
        cur.execute('''CREATE TEMPORARY TABLE tmp_student_answers (
            target_id BIGINT PRIMARY KEY, respostas INT, acertos INT)''')
        cur.executemany('''INSERT INTO tmp_student_answers
            (respostas,acertos,target_id) VALUES (%s,%s,%s)''', updates)
        cur.execute('''UPDATE alunos_simulados a
            JOIN tmp_student_answers s ON a.id=s.target_id
            SET a.TOTAL_QUESTAO_RESPONDIDA=COALESCE(a.TOTAL_QUESTAO_RESPONDIDA,s.respostas),
                a.TOTAL_ACERTOS=COALESCE(a.TOTAL_ACERTOS,s.acertos)''')
    return len(updates)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--students', action='store_true')
    parser.add_argument('--questions', action='store_true')
    parser.add_argument('--question-map', action='store_true')
    parser.add_argument('--question-details', action='store_true')
    parser.add_argument('--answers', action='store_true')
    parser.add_argument('--student-counts', action='store_true')
    parser.add_argument('--student-answers', action='store_true')
    args = parser.parse_args()
    schools, exams = read_source()
    conn = mysql_connection()
    try:
        cur = conn.cursor(dictionary=True)
        school_inserts, school_updates = sync_catalog(cur, schools, args.apply)
        school_names = {canonical(row['escola']): row['escola'] for row in schools}
        exam_inserts, exam_updates = sync_exams(cur, exams, school_names, args.apply)
        print({'schools_insert': school_inserts, 'schools_fill': school_updates,
               'exams_insert': exam_inserts, 'exams_fill': exam_updates,
               'applied': args.apply})
        if args.students:
            print({'students': sync_students(cur, school_names, args.apply),
                   'applied': args.apply}, flush=True)
        if args.questions:
            print({'question_skills': sync_question_skills(cur, args.apply),
                   'applied': args.apply}, flush=True)
        if args.question_map:
            print({'question_map_insert': sync_question_map(cur, school_names, args.apply),
                   'applied': args.apply}, flush=True)
        if args.question_details:
            print({'question_details_insert': sync_question_details(cur, school_names, args.apply),
                   'applied': args.apply}, flush=True)
        if args.answers:
            print({'question_answer_fill': sync_answer_counts(cur, args.apply),
                   'applied': args.apply}, flush=True)
        if args.student_counts:
            print({'student_question_totals': sync_student_question_totals(cur, args.apply),
                   'student_periods': sync_exam_periods(cur, args.apply),
                   'applied': args.apply}, flush=True)
        if args.student_answers:
            print({'student_answer_totals': sync_student_answer_totals(cur, args.apply),
                   'applied': args.apply}, flush=True)
        if args.apply:
            conn.commit()
        else:
            conn.rollback()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
