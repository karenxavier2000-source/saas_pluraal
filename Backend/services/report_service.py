"""Relatórios educacionais com comparações seguras por escopo."""
import re
import time
import unicodedata

from Backend.database.connection import get_db_cursor
from Backend.services.delegation_service import get_effective_user_scope

_REPORT_CACHE = {}
_CACHE_TTL = 1800  # 30 minutes


def clear_report_cache(user_id):
    """Remove cached report slices for one user before an explicit refresh."""
    for key in [key for key in _REPORT_CACHE if key[0] == user_id]:
        _REPORT_CACHE.pop(key, None)


SUBJECT_LABELS = {
    'lingua portuguesa': 'Língua Portuguesa',
    'matematica': 'Matemática',
    'fisica': 'Física',
    'quimica': 'Química',
    'biologia': 'Biologia',
    'linguagens, codigos e suas tecnologias': 'Linguagens, Códigos e suas Tecnologias',
    'ciencias humanas e suas tecnologias': 'Ciências Humanas e suas Tecnologias',
    'ciencias da natureza e suas tecnologias': 'Ciências da Natureza e suas Tecnologias',
    'matematica e suas tecnologias': 'Matemática e suas Tecnologias',
}


def _fold_label(value):
    clean = ' '.join((value or '').split())
    return ''.join(c for c in unicodedata.normalize('NFKD', clean.casefold())
                   if not unicodedata.combining(c))


def _subject(value):
    clean = ' '.join((value or '').split())
    return SUBJECT_LABELS.get(_fold_label(clean), clean or 'Não informada')


DIFFICULTY_LABELS = {
    'facil': 'Fácil', 'baixa': 'Fácil', 'baixo': 'Fácil',
    'medio': 'Médio', 'media': 'Médio',
    'dificil': 'Difícil', 'alta': 'Difícil', 'alto': 'Difícil',
}
DIFFICULTY_ORDER = {'Fácil': 0, 'Médio': 1, 'Difícil': 2}


def _difficulty(value):
    clean = ' '.join((value or '').split())
    return DIFFICULTY_LABELS.get(_fold_label(clean), clean or 'Não informada')


def _combine_answer_rows(rows, label_fields):
    buckets = {}
    for row in rows:
        labels = tuple((_subject(row[field]) if field == 'disciplina'
                        else _difficulty(row[field])) for field in label_fields)
        bucket = buckets.setdefault(labels, {'acertos': 0, 'erros': 0})
        bucket['acertos'] += row['acertos'] or 0
        bucket['erros'] += row['erros'] or 0
    result = []
    for labels, counts in buckets.items():
        total = counts['acertos'] + counts['erros']
        if total:
            result.append({**dict(zip(label_fields, labels)), **counts,
                           'taxa_acerto': round(100 * counts['acertos'] / total, 1)})
    if label_fields == ('dificuldade',):
        return sorted(result, key=lambda row: (DIFFICULTY_ORDER.get(row['dificuldade'], 99),
                                               row['dificuldade']))
    return sorted(result, key=lambda row: (-(row['acertos'] + row['erros']),
                                           *(row[field] for field in label_fields)))


def _student_key(ra, name):
    key = (ra or '').strip()
    if re.fullmatch(r'[0-9]+\.0+', key):
        key = key.split('.')[0]
    return key or 'nome:' + (name or '').strip().lower()


def _student_identity(alias):
    # Spreadsheet imports may turn an integer RA into text such as 4545.0.
    # Preserve meaningful characters/leading zeroes and normalize only zero decimals.
    return f"""COALESCE(CASE WHEN TRIM({alias}.ra) ~ '^[0-9]+[.]0+$'
        THEN SPLIT_PART(TRIM({alias}.ra), '.', 1)
        ELSE NULLIF(TRIM({alias}.ra), '') END, 'nome:' || LOWER(TRIM({alias}.alunos)))"""


def _subject_sql(alias):
    return f"""TRANSLATE(LOWER(REGEXP_REPLACE(TRIM(COALESCE({alias}.disciplina,'')),
        '\\s+', ' ', 'g')), 'áàãâäéèêëíìîïóòôõöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"""


def _skill_sql(alias):
    """Use the code embedded in a description when the imported skill is a topic label."""
    return f"""CASE WHEN TRIM(COALESCE({alias}.descricao,'')) ~* '^[0-9]+[A-Z][0-9]+[[:space:]]*[-–:]'
                    AND TRIM(COALESCE({alias}.habilidade,'')) !~* '^[0-9]+[A-Z][0-9]+$'
                THEN UPPER((REGEXP_MATCH(TRIM({alias}.descricao), '^([0-9]+[A-Za-z][0-9]+)', 'i'))[1])
                WHEN TRIM(COALESCE({alias}.habilidade,'')) !~ '[0-9]'
                     AND COALESCE({alias}.descricao,'') ~* '\\([A-Z]+[[:space:]]+C[0-9]+\\)'
                THEN UPPER((REGEXP_MATCH({alias}.descricao, '\\(([A-Z]+[[:space:]]+C[0-9]+)\\)', 'i'))[1])
                ELSE UPPER(TRIM({alias}.habilidade)) END"""


def _nivel_serie_sql(alias='a'):
    return f"""CASE 
        WHEN COALESCE({alias}.serie, {alias}.nivel_serie, '') ~ '9' THEN '2F ( 9ª Série )'
        WHEN COALESCE({alias}.serie, {alias}.nivel_serie, '') ~ '8' THEN '2F ( 8ª Série )'
        WHEN COALESCE({alias}.serie, {alias}.nivel_serie, '') ~ '7' THEN '2F ( 7ª Série )'
        WHEN COALESCE({alias}.serie, {alias}.nivel_serie, '') ~ '6' THEN '2F ( 6ª Série )'
        WHEN COALESCE({alias}.serie, {alias}.nivel_serie, '') ~ '5' THEN '1F ( 5ª Série )'
        WHEN COALESCE({alias}.serie, {alias}.nivel_serie, '') ~ '4' THEN '1F ( 4ª Série )'
        WHEN COALESCE({alias}.serie, {alias}.nivel_serie, '') ~ '3' AND (COALESCE({alias}.nivel, '') ~* 'EM|E[.]M' OR COALESCE({alias}.serie, '') ~* 'ANO') THEN 'E.M ( 3º Ano )'
        WHEN COALESCE({alias}.serie, {alias}.nivel_serie, '') ~ '3' THEN '1F ( 3ª Série )'
        WHEN COALESCE({alias}.serie, {alias}.nivel_serie, '') ~ '2' AND (COALESCE({alias}.nivel, '') ~* 'EM|E[.]M' OR COALESCE({alias}.serie, '') ~* 'ANO') THEN 'E.M ( 2º Ano )'
        WHEN COALESCE({alias}.serie, {alias}.nivel_serie, '') ~ '2' THEN '1F ( 2ª Série )'
        WHEN COALESCE({alias}.serie, {alias}.nivel_serie, '') ~ '1' AND (COALESCE({alias}.nivel, '') ~* 'EM|E[.]M' OR COALESCE({alias}.serie, '') ~* 'ANO') THEN 'E.M ( 1º Ano )'
        WHEN COALESCE({alias}.serie, {alias}.nivel_serie, '') ~ '1' THEN '1F ( 1ª Série )'
        ELSE COALESCE(NULLIF(TRIM({alias}.nivel_serie),''), NULLIF(TRIM({alias}.serie),''), 'Outros')
    END"""


def _format_skill(row):
    row = dict(row)
    description = row.get('descricao') or ''
    embedded_code = re.match(r'^\s*([0-9]+[A-Za-z][0-9]+)\s*[-–:]\s*(.*)', description)
    if embedded_code:
        code = embedded_code.group(1).upper()
        if row.get('habilidade') == code or not re.fullmatch(r'[0-9]+[A-Z][0-9]+', row.get('habilidade') or ''):
            row['habilidade'] = code
            row['descricao'] = embedded_code.group(2)
    else:
        embedded_competency = re.search(r'\(([A-Z]+\s+C\d+)\)', description, re.I)
        if embedded_competency and (row.get('habilidade') == embedded_competency.group(1).upper()
                                    or not re.search(r'\d', row.get('habilidade') or '')):
            row['habilidade'] = embedded_competency.group(1).upper()
            row['descricao'] = re.sub(r'\s*\(' + re.escape(embedded_competency.group(1)) + r'\)', '', description, count=1, flags=re.I).strip()
    total = row['acertos'] + row['erros']
    return {**row, 'disciplina': _subject(row['disciplina']), 'questoes': total,
            'alunos': row.get('alunos') or 0,
            'simulados': row.get('simulados') or 0,
            'taxa_acerto': round(100 * row['acertos'] / total, 1) if total else None}


def _institution_skills(cur, schools, period, values):
    names = [s['escola'].strip().lower() for s in schools]
    g_period = period.replace('a.', 'g.') if period else 'TRUE'
    include_students = (len(schools) == 1)

    grouping_sets = [
        "(disciplina,habilidade)",
        "(uniao,disciplina,habilidade)",
        "(uniao,associacao,disciplina,habilidade)",
        "(school_key,disciplina,habilidade)"
    ]
    if include_students:
        grouping_sets.append("(school_key,student_key,disciplina,habilidade)")

    student_sel = f"{_student_identity('g')} student_key, g.alunos nome, g.ra, g.turma, g.nivel_serie, g.id_simulado,"
    group_student_sql = "GROUPING(student_key) group_student" if include_students else "1 group_student"
    student_col_sql = "student_key," if include_students else "NULL::text student_key,"

    cur.execute(f'''WITH schools AS (
        SELECT * FROM UNNEST(%s::text[], %s::text[], %s::text[])
            AS s(school_key, uniao, associacao)
    ), answers AS (
        SELECT s.uniao, s.associacao, s.school_key,
            {student_sel}
            {_subject_sql('g')} disciplina,
            {_skill_sql('g')} habilidade,
            NULLIF(TRIM(g.descricao),'') descricao,
            g.status_questao
        FROM pluraal.gabarito_aluno g
        JOIN schools s ON s.school_key = LOWER(TRIM(g.escola))
        WHERE LOWER(TRIM(g.escola)) = ANY(%s)
          AND {g_period}
          AND g.status_questao IN ('ACERTO','ERRO')
          AND (NULLIF(TRIM(g.habilidade),'') IS NOT NULL
               OR TRIM(COALESCE(g.descricao,'')) ~* '^[0-9]+[A-Z][0-9]+[[:space:]]*[-–:]')
    )
    SELECT GROUPING(school_key) group_school, GROUPING(associacao) group_assoc,
        GROUPING(uniao) group_union, {group_student_sql}, school_key, {student_col_sql} uniao, associacao, disciplina, habilidade,
        MAX(descricao) descricao,
        MAX(nome) nome, MAX(ra) ra, MAX(turma) turma, MAX(nivel_serie) nivel_serie,
        COUNT(*) FILTER (WHERE status_questao='ACERTO') acertos,
        COUNT(*) FILTER (WHERE status_questao='ERRO') erros,
        COUNT(DISTINCT student_key) alunos,
        COUNT(DISTINCT id_simulado) simulados
    FROM answers GROUP BY GROUPING SETS ({", ".join(grouping_sets)})''',
    [names, [s['uniao'] for s in schools], [s['associacao'] for s in schools], names] + values)
    result = {level: [] for level in ('geral','uniao','associacao','escola','aluno')}
    school_map = {s['escola'].strip().lower(): s for s in schools}
    for raw in cur.fetchall():
        level = ('aluno' if not raw.pop('group_student') else
                 'escola' if not raw.pop('group_school') else
                 'associacao' if not raw['group_assoc'] else 'uniao' if not raw['group_union'] else 'geral')
        raw.pop('group_assoc'); raw.pop('group_union')
        if level in ('escola', 'aluno'):
            school = school_map[raw['school_key']]
            raw.update(escola=school['escola'], uniao=school['uniao'], associacao=school['associacao'])
        result[level].append(_format_skill(raw))
    for rows in result.values():
        rows.sort(key=lambda r: (r['taxa_acerto'], -r['questoes'], r['disciplina'], r['habilidade']))
    return result


def _catalog(cur):
    cur.execute('''SELECT id_escolas, "ESCOLA" escola, "SIGLA_UNIAO" uniao,
                       "SIGLA_ASSOCIACAO" associacao
                FROM pluraal.escolas_pluraal
                WHERE "SIGLA_UNIAO" IS NOT NULL AND "SIGLA_UNIAO" <> 'SIGLA_UNIAO'
                ORDER BY 3,4,2''')
    return cur.fetchall()


def _matches_filter(val, filter_val):
    if not filter_val:
        return True
    if isinstance(filter_val, (list, set, tuple)):
        return val in filter_val
    if isinstance(filter_val, str) and ',' in filter_val:
        items = [x.strip() for x in filter_val.split(',') if x.strip()]
        return val in items
    return str(val).strip().lower() == str(filter_val).strip().lower()


def _matches_school(r, filter_val):
    if not filter_val:
        return True
    items = filter_val if isinstance(filter_val, (list, set, tuple)) else [x.strip() for x in str(filter_val).split(',') if x.strip()]
    for item in items:
        if str(r.get('id_escolas')) == str(item) or r.get('escola', '').strip().lower() == str(item).strip().lower():
            return True
    return False


def _scope_rows(catalog, scope, filters):
    own = catalog if scope['hierarquia'] in ('Master', 'Administrador') else [r for r in catalog if r['id_escolas'] in scope['escolas']]
    preview = None
    if scope.get('is_simulated'):
        if filters.get('preview_nivel') and filters['preview_nivel'] != scope['hierarquia']:
            raise PermissionError('Nível de simulação inválido.')
        preview = {'uniao': None, 'associacao': None, 'id_escolas': None} if scope['hierarquia'] == 'Administrador' else (own[0] if own else None)
    elif filters.get('preview_nivel'):
        raise PermissionError('A simulação solicitada não foi autorizada.')
    selected = [r for r in own if _matches_filter(r['uniao'], filters.get('uniao'))
                and _matches_filter(r['associacao'], filters.get('associacao'))
                and _matches_school(r, filters.get('escola'))]
    return own, selected, preview


def _period(filters):
    clauses, values = [], []
    for field in ('ano', 'bimestre', 'serie', 'turma'):
        if filters.get(field):
            val = filters[field]
            if isinstance(val, (list, tuple, set)):
                clauses.append(f'a.{field} = ANY(%s)')
                values.append(list(val))
            elif isinstance(val, str) and ',' in val:
                clauses.append(f'a.{field} = ANY(%s)')
                values.append([x.strip() for x in val.split(',') if x.strip()])
            else:
                clauses.append(f'a.{field} = %s')
                values.append(val)
    return ' AND '.join(clauses) or 'TRUE', values


def _attempts(period):
    # Subject rows are collapsed to one student/school/exam attempt.
    return f'''WITH base_attempts AS (
        SELECT LOWER(TRIM(a.escola)) school_key,
               {_student_identity('a')} student_key,
               a.id_simulado, MAX(a.alunos) nome, MAX(a.ra) ra,
               MAX(a.serie) serie,
               MAX({_nivel_serie_sql('a')}) nivel_serie,
               MAX(a.turma) turma,
               MAX(a.bimestre) bimestre, MAX(a.nome_simulado) nome_simulado,
               MAX(a.inicio) inicio,
               COALESCE(
                   MAX(a.total_final) FILTER (WHERE a.total_final IS NOT NULL),
                   MAX(a.nota_disciplina) FILTER (WHERE LOWER(TRIM(COALESCE(a.disciplina,''))) IN ('total', 'total ()', 'total geral') AND a.nota_disciplina IS NOT NULL),
                   ROUND(100.0 * SUM(a.qtd_acertos_disciplina) FILTER (WHERE LOWER(TRIM(COALESCE(a.disciplina,''))) NOT IN ('total', 'total ()', 'total geral')) / NULLIF(SUM(a.qtd_questao_disciplina) FILTER (WHERE LOWER(TRIM(COALESCE(a.disciplina,''))) NOT IN ('total', 'total ()', 'total geral')), 0), 2)
               ) nota,
               COALESCE(
                   MAX(a.total_acertos) FILTER (WHERE a.total_acertos IS NOT NULL),
                   MAX(a.qtd_acertos_disciplina) FILTER (WHERE LOWER(TRIM(COALESCE(a.disciplina,''))) IN ('total', 'total ()', 'total geral') AND a.qtd_acertos_disciplina IS NOT NULL),
                   SUM(a.qtd_acertos_disciplina) FILTER (WHERE LOWER(TRIM(COALESCE(a.disciplina,''))) NOT IN ('total', 'total ()', 'total geral'))
               ) acertos,
               COALESCE(
                   MAX(a.total_questao) FILTER (WHERE a.total_questao IS NOT NULL),
                   MAX(a.qtd_questao_disciplina) FILTER (WHERE LOWER(TRIM(COALESCE(a.disciplina,''))) IN ('total', 'total ()', 'total geral') AND a.qtd_questao_disciplina IS NOT NULL),
                   SUM(a.qtd_questao_disciplina) FILTER (WHERE LOWER(TRIM(COALESCE(a.disciplina,''))) NOT IN ('total', 'total ()', 'total geral'))
               ) questoes
        FROM pluraal.aluno a
        WHERE LOWER(TRIM(a.escola)) = ANY(%s)
          AND a.id_simulado IS NOT NULL AND {period}
        GROUP BY 1,2,3
    ),
    attempts AS (
        SELECT * FROM base_attempts
    )'''


def _build_ranking(rows, group_key_func, name_key, own_check_func, mask_others):
    groups = {}
    for r in rows:
        k = group_key_func(r)
        item = groups.setdefault(k, {
            'name': r[name_key], 'students': 0, 'hits': 0, 'questions': 0,
            'expected': 0, 'completed': 0, 'sum_nota': 0, 'count_nota': 0, 'own': False
        })
        item['students'] += r['students']
        item['expected'] += r.get('expected', 0)
        item['completed'] += r.get('completed', 0)
        item['hits'] += r['hits']
        item['questions'] += r['questions']
        item['sum_nota'] += float(r.get('sum_nota', 0))
        item['count_nota'] += r.get('count_nota', 0)
        if own_check_func(k, r):
            item['own'] = True

    ordered = sorted(
        groups.items(),
        key=lambda pair: (
            pair[1]['count_nota'] == 0,
            -float(pair[1]['sum_nota']) / float(pair[1]['count_nota']) if pair[1]['count_nota'] else 0,
            pair[0]
        )
    )

    result = []
    for pos, (k, item) in enumerate(ordered, 1):
        is_own = item['own'] or not mask_others
        result.append({
            'posicao': pos if item['count_nota'] else None,
            'nome': item['name'] if is_own else 'Instituição reservada',
            'alunos': item['students'] if is_own else None,
            'esperados': item['expected'] if is_own else None,
            'fizeram': item['completed'] if is_own else None,
            'media_acerto': round(float(item['sum_nota']) / float(item['count_nota']), 1) if item['count_nota'] and is_own else None,
            'proprio': is_own
        })
    return result


def _empty(profile, own, selected, catalog, preview):
    return {'perfil': profile, 'simulando': bool(preview), 'entidades_acessiveis': own,
            'entidades_catalogo': catalog,
            'kpis': {'total_alunos': 0, 'total_escolas': len(selected), 'total_simulados': 0,
                     'simulados_respondidos': 0, 'simulados_nao_respondidos': 0,
                     'media_geral': 0, 'participacao': 0, 'questoes_respondidas': 0},
            'por_disciplina': [], 'por_dificuldade': [], 'matriz_disciplina_dificuldade': [],
            'rankings': {}, 'melhores_alunos': [], 'alunos_atencao': [], 'alunos_pendentes': [],
            'participacao_bimestre': [], 'evolucao_bimestre': [], 'por_serie': [], 'por_turma': [],
            'analise_bimestral': {'bimestres_lista': [], 'evolucao_rede': [], 'por_uniao': [],
                                  'por_associacao': [], 'por_escola': [], 'por_aluno': {},
                                  'comparativo_anos': {'tem_dados_2025': False, 'anos': ['2026', '2025'], 'linhas': []}},
            'escolas_resumo': [], 'criterio_minimo_questoes': 0,
            'habilidades_por_nivel': {level: [] for level in ('geral','uniao','associacao','escola')}}


def _build_bimonthly_analysis(cur, names, school_map, selected, own, peers, catalog, data_bimestres):
    try:
        cur.execute('''
            SELECT school_key, ano, bimestre,
                   COUNT(DISTINCT student_key) students,
                   COUNT(DISTINCT student_key) FILTER (WHERE nota IS NOT NULL AND questoes > 0) completed,
                   COUNT(DISTINCT id_simulado) FILTER (WHERE nota IS NOT NULL AND questoes > 0) exams,
                   SUM(COALESCE(acertos, 0)) hits,
                   SUM(questoes) FILTER (WHERE nota IS NOT NULL AND questoes > 0) questions,
                   SUM(COALESCE(nota, 0)) sum_nota, COUNT(nota) count_nota
            FROM tmp_attempts_report
            WHERE school_key = ANY(%s) AND bimestre IS NOT NULL
            GROUP BY 1, 2, 3
            ORDER BY 2, 3
        ''', [names])
        rows = cur.fetchall()

        all_bimestres = sorted(list(set(r['bimestre'] for r in rows if r['bimestre'])))
        if not all_bimestres:
            all_bimestres = [b for b in data_bimestres if b]

        # 1. Evolução Consolidada por Bimestre no Escopo Selecionado
        bim_totals = {}
        for r in rows:
            b = r['bimestre']
            bt = bim_totals.setdefault(b, {'bimestre': b, 'alunos': 0, 'fizeram': 0, 'simulados': 0, 'hits': 0.0, 'questions': 0.0, 'sum_nota': 0.0, 'count_nota': 0})
            bt['alunos'] += (r['students'] or 0)
            bt['fizeram'] += (r['completed'] or 0)
            bt['simulados'] += (r['exams'] or 0)
            bt['hits'] += float(r['hits'] or 0)
            bt['questions'] += float(r['questions'] or 0)
            bt['sum_nota'] += float(r['sum_nota'] or 0)
            bt['count_nota'] += (r['count_nota'] or 0)

        evolucao_rede = []
        prev_taxa = None
        for b in all_bimestres:
            bt = bim_totals.get(b, {'bimestre': b, 'alunos': 0, 'fizeram': 0, 'simulados': 0, 'hits': 0.0, 'questions': 0.0, 'sum_nota': 0.0, 'count_nota': 0})
            taxa = round(bt['sum_nota'] / bt['count_nota'], 1) if bt['count_nota'] else None
            part = round(100.0 * bt['fizeram'] / bt['alunos'], 1) if bt['alunos'] else 0
            delta = round(taxa - prev_taxa, 1) if (taxa is not None and prev_taxa is not None) else None
            if taxa is not None:
                prev_taxa = taxa
            evolucao_rede.append({
                'bimestre': b,
                'taxa_acerto': taxa,
                'participacao': part,
                'alunos': bt['alunos'],
                'fizeram': bt['fizeram'],
                'simulados': bt['simulados'],
                'delta': delta
            })

        # 2. Desempenho por União por Bimestre
        uniao_map = {}
        for r in rows:
            sinfo = school_map.get(r['school_key'])
            if not sinfo or not sinfo.get('uniao'):
                continue
            u = sinfo['uniao']
            b = r['bimestre']
            u_entry = uniao_map.setdefault(u, {'uniao': u, 'bimestres': {}, 'hits': 0.0, 'questions': 0.0, 'sum_nota': 0.0, 'count_nota': 0, 'fizeram': 0, 'alunos': 0})
            ub = u_entry['bimestres'].setdefault(b, {'hits': 0.0, 'questions': 0.0, 'sum_nota': 0.0, 'count_nota': 0, 'fizeram': 0, 'alunos': 0, 'simulados': 0})
            hits_val = float(r['hits'] or 0)
            q_val = float(r['questions'] or 0)
            sum_n = float(r['sum_nota'] or 0)
            cnt_n = (r['count_nota'] or 0)
            ub['hits'] += hits_val
            ub['questions'] += q_val
            ub['sum_nota'] += sum_n
            ub['count_nota'] += cnt_n
            ub['fizeram'] += (r['completed'] or 0)
            ub['alunos'] += (r['students'] or 0)
            ub['simulados'] += (r['exams'] or 0)
            u_entry['hits'] += hits_val
            u_entry['questions'] += q_val
            u_entry['sum_nota'] += sum_n
            u_entry['count_nota'] += cnt_n
            u_entry['fizeram'] += (r['completed'] or 0)
            u_entry['alunos'] += (r['students'] or 0)

        unioes_resumo = []
        for u, u_data in uniao_map.items():
            bims_dict = {}
            p_taxa = None
            for b in all_bimestres:
                bd = u_data['bimestres'].get(b)
                if bd and bd['count_nota']:
                    t = round(bd['sum_nota'] / bd['count_nota'], 1)
                    d = round(t - p_taxa, 1) if p_taxa is not None else None
                    p_taxa = t
                    bims_dict[b] = {'taxa_acerto': t, 'delta': d, 'fizeram': bd['fizeram'], 'simulados': bd['simulados']}
                else:
                    bims_dict[b] = {'taxa_acerto': None, 'delta': None, 'fizeram': 0, 'simulados': 0}
            media_geral = round(u_data['sum_nota'] / u_data['count_nota'], 1) if u_data['count_nota'] else 0
            unioes_resumo.append({
                'uniao': u,
                'media_geral': media_geral,
                'fizeram_total': u_data['fizeram'],
                'bimestres': bims_dict
            })
        unioes_resumo.sort(key=lambda x: -x['media_geral'])

        # 3. Desempenho por Associação por Bimestre
        assoc_map = {}
        for r in rows:
            sinfo = school_map.get(r['school_key'])
            if not sinfo or not sinfo.get('associacao'):
                continue
            u = sinfo.get('uniao', '')
            a = sinfo['associacao']
            key = (u, a)
            a_entry = assoc_map.setdefault(key, {'associacao': a, 'uniao': u, 'bimestres': {}, 'hits': 0.0, 'questions': 0.0, 'sum_nota': 0.0, 'count_nota': 0, 'fizeram': 0, 'alunos': 0})
            ab = a_entry['bimestres'].setdefault(r['bimestre'], {'hits': 0.0, 'questions': 0.0, 'sum_nota': 0.0, 'count_nota': 0, 'fizeram': 0, 'alunos': 0, 'simulados': 0})
            hits_val = float(r['hits'] or 0)
            q_val = float(r['questions'] or 0)
            ab['hits'] += hits_val
            ab['questions'] += q_val
            ab['sum_nota'] += float(r['sum_nota'] or 0)
            ab['count_nota'] += (r['count_nota'] or 0)
            ab['fizeram'] += (r['completed'] or 0)
            ab['alunos'] += (r['students'] or 0)
            ab['simulados'] += (r['exams'] or 0)
            a_entry['hits'] += hits_val
            a_entry['questions'] += q_val
            a_entry['sum_nota'] += float(r['sum_nota'] or 0)
            a_entry['count_nota'] += (r['count_nota'] or 0)
            a_entry['fizeram'] += (r['completed'] or 0)
            a_entry['alunos'] += (r['students'] or 0)

        assocs_resumo = []
        for (u, a), a_data in assoc_map.items():
            bims_dict = {}
            p_taxa = None
            for b in all_bimestres:
                bd = a_data['bimestres'].get(b)
                if bd and bd['count_nota']:
                    t = round(bd['sum_nota'] / bd['count_nota'], 1)
                    d = round(t - p_taxa, 1) if p_taxa is not None else None
                    p_taxa = t
                    bims_dict[b] = {'taxa_acerto': t, 'delta': d, 'fizeram': bd['fizeram'], 'simulados': bd['simulados']}
                else:
                    bims_dict[b] = {'taxa_acerto': None, 'delta': None, 'fizeram': 0, 'simulados': 0}
            media_geral = round(a_data['sum_nota'] / a_data['count_nota'], 1) if a_data['count_nota'] else 0
            assocs_resumo.append({
                'associacao': a,
                'uniao': u,
                'media_geral': media_geral,
                'fizeram_total': a_data['fizeram'],
                'bimestres': bims_dict
            })
        assocs_resumo.sort(key=lambda x: -x['media_geral'])

        # 4. Desempenho por Escola por Bimestre
        escola_bim_map = {}
        for r in rows:
            sinfo = school_map.get(r['school_key'])
            if not sinfo:
                continue
            esc_id = sinfo['id_escolas']
            e_entry = escola_bim_map.setdefault(esc_id, {
                'id_escolas': esc_id, 'escola': sinfo['escola'], 'uniao': sinfo.get('uniao'),
                'associacao': sinfo.get('associacao'), 'bimestres': {}, 'hits': 0.0, 'questions': 0.0, 'sum_nota': 0.0, 'count_nota': 0, 'fizeram': 0
            })
            eb = e_entry['bimestres'].setdefault(r['bimestre'], {'hits': 0.0, 'questions': 0.0, 'sum_nota': 0.0, 'count_nota': 0, 'fizeram': 0, 'alunos': 0, 'simulados': 0})
            hits_val = float(r['hits'] or 0)
            q_val = float(r['questions'] or 0)
            eb['hits'] += hits_val
            eb['questions'] += q_val
            eb['sum_nota'] += float(r['sum_nota'] or 0)
            eb['count_nota'] += (r['count_nota'] or 0)
            eb['fizeram'] += (r['completed'] or 0)
            eb['simulados'] += (r['exams'] or 0)
            e_entry['hits'] += hits_val
            e_entry['questions'] += q_val
            e_entry['sum_nota'] += float(r['sum_nota'] or 0)
            e_entry['count_nota'] += (r['count_nota'] or 0)
            e_entry['fizeram'] += (r['completed'] or 0)

        escolas_resumo = []
        for esc_id, e_data in escola_bim_map.items():
            bims_dict = {}
            p_taxa = None
            for b in all_bimestres:
                bd = e_data['bimestres'].get(b)
                if bd and bd['count_nota']:
                    t = round(bd['sum_nota'] / bd['count_nota'], 1)
                    d = round(t - p_taxa, 1) if p_taxa is not None else None
                    p_taxa = t
                    bims_dict[b] = {'taxa_acerto': t, 'delta': d, 'fizeram': bd['fizeram'], 'simulados': bd['simulados']}
                else:
                    bims_dict[b] = {'taxa_acerto': None, 'delta': None, 'fizeram': 0, 'simulados': 0}
            media_geral = round(e_data['sum_nota'] / e_data['count_nota'], 1) if e_data['count_nota'] else 0
            escolas_resumo.append({
                'id_escolas': esc_id,
                'escola': e_data['escola'],
                'uniao': e_data['uniao'],
                'associacao': e_data['associacao'],
                'media_geral': media_geral,
                'fizeram_total': e_data['fizeram'],
                'bimestres': bims_dict
            })
        escolas_resumo.sort(key=lambda x: -x['media_geral'])

        # 5. Desempenho por Aluno por Bimestre
        cur.execute('''
            SELECT bimestre, school_key, student_key, MAX(nome) nome,
                   MAX(nivel_serie) nivel_serie, MAX(turma) turma,
                   COUNT(DISTINCT id_simulado) simulados,
                   SUM(acertos) hits, SUM(questoes) questions,
                   SUM(nota) sum_nota, COUNT(nota) count_nota
            FROM tmp_attempts_report
            WHERE school_key = ANY(%s) AND bimestre IS NOT NULL AND nota IS NOT NULL AND questoes >= 12
            GROUP BY 1, 2, 3
            ORDER BY 1, (SUM(nota)::float / NULLIF(COUNT(nota), 0)) DESC
        ''', [names])
        student_bim_rows = cur.fetchall()
        alunos_por_bimestre = {}
        for r in student_bim_rows:
            b = r['bimestre']
            taxa = round(float(r['sum_nota']) / r['count_nota'], 1) if r['count_nota'] else None
            sinfo = school_map.get(r['school_key'])
            esc_nome = sinfo['escola'] if sinfo else r['school_key']
            b_list = alunos_por_bimestre.setdefault(b, [])
            if len(b_list) < 15:
                b_list.append({
                    'nome': r['nome'],
                    'escola': esc_nome,
                    'serie': r['nivel_serie'],
                    'turma': r['turma'],
                    'simulados': r['simulados'],
                    'questoes': r['questions'],
                    'taxa_acerto': taxa
                })

        # Alunos com evolução longitudinal (participaram de >= 2 bimestres)
        cur.execute('''
            SELECT school_key, student_key, MAX(nome) nome,
                   MAX(nivel_serie) nivel_serie, MAX(turma) turma,
                   ARRAY_AGG(bimestre ORDER BY bimestre) bims,
                   ARRAY_AGG(ROUND(sum_nota::numeric / NULLIF(count_nota, 0), 1) ORDER BY bimestre) notas
            FROM (
                SELECT school_key, student_key, bimestre, MAX(nome) nome,
                       MAX(nivel_serie) nivel_serie, MAX(turma) turma,
                       SUM(nota) sum_nota, COUNT(nota) count_nota
                FROM tmp_attempts_report
                WHERE school_key = ANY(%s) AND bimestre IS NOT NULL AND nota IS NOT NULL AND questoes >= 10
                GROUP BY 1, 2, 3
            ) sub
            GROUP BY 1, 2
            HAVING COUNT(DISTINCT bimestre) >= 2
            ORDER BY MAX(nome)
            LIMIT 40
        ''', [names])
        alunos_evolucao = []
        for r in cur.fetchall():
            sinfo = school_map.get(r['school_key'])
            esc_nome = sinfo['escola'] if sinfo else r['school_key']
            bims = r['bims'] or []
            notas = [float(n) if n is not None else None for n in (r['notas'] or [])]
            delta_aluno = round(notas[-1] - notas[0], 1) if (len(notas) >= 2 and notas[-1] is not None and notas[0] is not None) else 0
            alunos_evolucao.append({
                'nome': r['nome'],
                'escola': esc_nome,
                'serie': r['nivel_serie'],
                'turma': r['turma'],
                'bimestres': bims,
                'notas': notas,
                'delta': delta_aluno
            })
        alunos_evolucao.sort(key=lambda x: -x['delta'])

        # 6. Comparativo por Bimestre e Ano (ex: 2026 vs 2025)
        distinct_anos = sorted(list(set(r['ano'] for r in rows if r['ano'])), reverse=True)
        if '2026' not in distinct_anos:
            distinct_anos.insert(0, '2026')
        if '2025' not in distinct_anos:
            distinct_anos.append('2025')

        ano_bim_map = {}
        for r in rows:
            key = (r['ano'], r['bimestre'])
            ab = ano_bim_map.setdefault(key, {'sum_nota': 0.0, 'count_nota': 0, 'students': 0, 'completed': 0, 'exams': 0})
            ab['sum_nota'] += float(r['sum_nota'] or 0)
            ab['count_nota'] += r['count_nota'] or 0
            ab['students'] += (r['students'] or 0)
            ab['completed'] += (r['completed'] or 0)
            ab['exams'] += (r['exams'] or 0)

        tem_dados_2025 = any(v['count_nota'] > 0 for k, v in ano_bim_map.items() if k[0] == '2025')

        comparativo_anos = []
        for b in all_bimestres:
            dados_2026 = ano_bim_map.get(('2026', b))
            taxa_2026 = round(dados_2026['sum_nota'] / dados_2026['count_nota'], 1) if (dados_2026 and dados_2026['count_nota']) else None
            
            dados_2025 = ano_bim_map.get(('2025', b))
            taxa_2025 = round(dados_2025['sum_nota'] / dados_2025['count_nota'], 1) if (dados_2025 and dados_2025['count_nota']) else None
            
            delta_interanual = round(taxa_2026 - taxa_2025, 1) if (taxa_2026 is not None and taxa_2025 is not None) else None

            comparativo_anos.append({
                'bimestre': b,
                'ano_atual': {
                    'ano': '2026',
                    'taxa_acerto': taxa_2026,
                    'alunos': dados_2026['students'] if dados_2026 else 0,
                    'fizeram': dados_2026['completed'] if dados_2026 else 0,
                    'simulados': dados_2026['exams'] if dados_2026 else 0,
                },
                'ano_anterior': {
                    'ano': '2025',
                    'taxa_acerto': taxa_2025,
                    'alunos': dados_2025['students'] if dados_2025 else 0,
                    'fizeram': dados_2025['completed'] if dados_2025 else 0,
                    'simulados': dados_2025['exams'] if dados_2025 else 0,
                    'status': 'Disponível' if taxa_2025 is not None else 'Aguardando importação'
                },
                'delta_ano': delta_interanual
            })

        return {
            'bimestres_lista': all_bimestres,
            'evolucao_rede': evolucao_rede,
            'por_uniao': unioes_resumo,
            'por_associacao': assocs_resumo,
            'por_escola': escolas_resumo,
            'por_aluno': alunos_por_bimestre,
            'alunos_evolucao': alunos_evolucao,
            'comparativo_anos': {
                'tem_dados_2025': tem_dados_2025,
                'anos': distinct_anos,
                'linhas': comparativo_anos
            }
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Erro ao gerar analise bimestral: %s", e)
        return {
            'bimestres_lista': [b for b in data_bimestres if b],
            'evolucao_rede': [],
            'por_uniao': [],
            'por_associacao': [],
            'por_escola': [],
            'por_aluno': {},
            'alunos_evolucao': [],
            'comparativo_anos': {'tem_dados_2025': False, 'anos': ['2026', '2025'], 'linhas': []}
        }


def get_reports_data(user_id: int, filters: dict = None):
    filters = filters or {}
    with get_db_cursor(commit=False) as cur:
        base_scope = get_effective_user_scope(user_id, cur)
        scope = get_effective_user_scope(user_id, cur, allow_simulation=True)
        cache_key = (user_id, frozenset(filters.items()), scope['hierarquia'],
                     frozenset(scope['escolas']), bool(scope.get('is_simulated')),
                     bool(base_scope.get('pode_simular_visao')))
        now = time.time()
        if cache_key in _REPORT_CACHE:
            cached_time, cached_data = _REPORT_CACHE[cache_key]
            if now - cached_time < _CACHE_TTL:
                return cached_data
        catalog = _catalog(cur)
        own, selected, preview = _scope_rows(catalog, scope, filters)
        # Determinar a visão ativa:
        if preview and filters.get('preview_nivel'):
            vision = 'Master' if filters['preview_nivel'] == 'Administrador' else filters['preview_nivel']
        elif scope['hierarquia'] in ('uniao', 'associacao', 'escola'):
            if filters.get('escola'):
                vision = 'escola'
            elif filters.get('associacao'):
                vision = 'associacao'
            else:
                vision = scope['hierarquia']
        else:
            # Master sem preview: ajusta de acordo com o filtro aplicado
            if filters.get('escola'):
                vision = 'escola'
            elif filters.get('associacao'):
                vision = 'associacao'
            elif filters.get('uniao'):
                vision = 'uniao'
            else:
                vision = 'Master'

        # Identificar entidades de foco (União, Associação, Escola)
        target_uniao = None
        target_assoc = None
        target_escola = None

        if preview:
            target_uniao = preview.get('uniao')
            target_assoc = preview.get('associacao')
            target_escola = str(preview['id_escolas']) if preview.get('id_escolas') is not None else None
        else:
            cand_school = selected[0] if selected else (own[0] if own else None)
            if filters.get('uniao'):
                target_uniao = filters['uniao']
            elif cand_school:
                target_uniao = cand_school['uniao']

            if filters.get('associacao'):
                target_assoc = filters['associacao']
                if not target_uniao:
                    for r in catalog:
                        if r['associacao'] == target_assoc:
                            target_uniao = r['uniao']
                            break
            elif cand_school and vision in ('associacao', 'escola'):
                target_assoc = cand_school['associacao']

            if filters.get('escola'):
                target_escola = str(filters['escola'])
                for r in catalog:
                    if str(r['id_escolas']) == target_escola or r['escola'].strip().lower() == target_escola.strip().lower():
                        target_escola = str(r['id_escolas'])
                        target_assoc = r['associacao']
                        target_uniao = r['uniao']
                        break
            elif cand_school and vision == 'escola':
                target_escola = str(cand_school['id_escolas'])

        profile = 'Administrador' if scope.get('is_simulated') and scope['hierarquia'] == 'Administrador' else vision
        simulation_catalog = [r for r in catalog if r['id_escolas'] in base_scope['escolas']]
        data = _empty(profile, own, selected,
                      simulation_catalog if base_scope['hierarquia'] == 'Master' or base_scope.get('pode_simular_visao') else [], preview)
        data['visao'] = vision
        cur.execute('SELECT DISTINCT ano FROM pluraal.aluno WHERE ano IS NOT NULL ORDER BY ano DESC')
        data['anos_disponiveis'] = [r['ano'] for r in cur.fetchall()]
        cur.execute('SELECT DISTINCT bimestre FROM pluraal.aluno WHERE bimestre IS NOT NULL ORDER BY bimestre')
        data['bimestres_disponiveis'] = [r['bimestre'] for r in cur.fetchall()]
        if not selected:
            return data
        names = [r['escola'].strip().lower() for r in selected]
        school_map = {r['escola'].strip().lower(): r for r in selected}
        period, period_values = _period(filters)

        if vision == 'Master':
            peers = catalog
        elif vision == 'uniao':
            peers = catalog  # Para calcular a posição da União no ranking nacional de todas as uniões
        elif vision == 'associacao':
            # Escolas da própria união para comparar a associação entre as da mesma união
            peers = [r for r in catalog if r['uniao'] == target_uniao] if target_uniao else catalog
        elif vision == 'escola':
            # Escolas da associação para comparar a escola entre as escolas da associação
            peers = [r for r in catalog if (not target_uniao or r['uniao'] == target_uniao) and (not target_assoc or r['associacao'] == target_assoc)] if target_assoc else catalog
        else:
            peers = catalog

        peer_names = [r['escola'].strip().lower() for r in peers]

        cur.execute("DROP TABLE IF EXISTS tmp_attempts_report;")
        cur.execute(f'''CREATE TEMP TABLE tmp_attempts_report ON COMMIT DROP AS 
            SELECT * FROM (
                SELECT sub.*
                FROM (
                    SELECT LOWER(TRIM(a.escola)) school_key,
                           {_student_identity('a')} student_key,
                           a.id_simulado, MAX(a.alunos) nome, MAX(a.ra) ra,
                           MAX(a.serie) serie,
                           MAX({_nivel_serie_sql('a')}) nivel_serie,
                           MAX(a.turma) turma,
                           MAX(COALESCE(a.ano, '2026')) ano,
                           MAX(a.bimestre) bimestre, MAX(a.nome_simulado) nome_simulado,
                           MAX(a.inicio) inicio,
                           MAX(a.total_final) FILTER (WHERE a.total_final IS NOT NULL) nota,
                           COALESCE(
                               MAX(a.total_acertos) FILTER (WHERE a.total_acertos IS NOT NULL),
                               MAX(a.qtd_acertos_disciplina) FILTER (WHERE LOWER(TRIM(COALESCE(a.disciplina,''))) IN ('total', 'total ()', 'total geral') AND a.qtd_acertos_disciplina IS NOT NULL),
                               SUM(a.qtd_acertos_disciplina) FILTER (WHERE LOWER(TRIM(COALESCE(a.disciplina,''))) NOT IN ('total', 'total ()', 'total geral'))
                           ) acertos,
                           COALESCE(
                               MAX(a.total_questao) FILTER (WHERE a.total_questao IS NOT NULL),
                               MAX(a.qtd_questao_disciplina) FILTER (WHERE LOWER(TRIM(COALESCE(a.disciplina,''))) IN ('total', 'total ()', 'total geral') AND a.qtd_questao_disciplina IS NOT NULL),
                               SUM(a.qtd_questao_disciplina) FILTER (WHERE LOWER(TRIM(COALESCE(a.disciplina,''))) NOT IN ('total', 'total ()', 'total geral'))
                           ) questoes
                    FROM pluraal.aluno a
                    WHERE LOWER(TRIM(a.escola)) = ANY(%s)
                      AND a.id_simulado IS NOT NULL AND {period}
                    GROUP BY 1,2,3
                ) sub
            ) filtered
        ''', [peer_names] + period_values)
        cur.execute('CREATE INDEX idx_tmp_att_s ON tmp_attempts_report(school_key)')

        sql = "WITH attempts AS (SELECT * FROM tmp_attempts_report WHERE school_key = ANY(%s)) "

        # Expected means present in aluno; completed requires a recorded result.
        params = [names]
        year_sql = ''
        if filters.get('ano'):
            year_sql = 'AND a.ano = %s'
            params.append(filters['ano'])
        bim_sql = ''
        if filters.get('bimestre'):
            bim_sql = 'AND a.bimestre = %s'
            params.append(filters['bimestre'])
        cur.execute(f'''SELECT LOWER(TRIM(a.escola)) school_key, a.bimestre,
            COUNT(DISTINCT {_student_identity('a')}) expected,
            COUNT(DISTINCT {_student_identity('a')})
              FILTER (WHERE (a.total_final IS NOT NULL OR a.nota_disciplina IS NOT NULL)
                        AND COALESCE(a.total_questao, a.qtd_questao_disciplina, 0) > 0) completed
            FROM pluraal.aluno a
            WHERE LOWER(TRIM(a.escola)) = ANY(%s) AND a.bimestre IS NOT NULL
              {year_sql} {bim_sql}
            GROUP BY 1,2''', params)
        participation = {}
        for r in cur.fetchall():
            bucket = participation.setdefault(r['bimestre'], {'bimestre': r['bimestre'], 'esperados': 0, 'fizeram': 0, 'escolas': []})
            bucket['esperados'] += r['expected']
            bucket['fizeram'] += r['completed']
            school = school_map[r['school_key']]
            bucket['escolas'].append({'id_escolas': school['id_escolas'], 'escola': school['escola'],
                                      'esperados': r['expected'], 'fizeram': r['completed']})
        for name in ([filters['bimestre']] if filters.get('bimestre') else data['bimestres_disponiveis']):
            bucket = participation.setdefault(name, {'bimestre': name, 'esperados': 0, 'fizeram': 0, 'escolas': []})
            included = {r['id_escolas'] for r in bucket['escolas']}
            bucket['escolas'].extend({'id_escolas': school['id_escolas'], 'escola': school['escola'],
                                      'esperados': 0, 'fizeram': 0} for school in selected
                                     if school['id_escolas'] not in included)
            bucket['escolas'].sort(key=lambda r: r['escola'])
        data['participacao_bimestre'] = [participation[k] for k in sorted(participation)]

        cur.execute(sql + '''SELECT COUNT(DISTINCT (school_key, student_key)) students,
            COUNT(DISTINCT (school_key, student_key)) FILTER (WHERE nota IS NOT NULL AND questoes > 0) completed,
            COUNT(*) expected_exams,
            COUNT(*) FILTER (WHERE nota IS NOT NULL AND questoes > 0) exams,
            SUM(COALESCE(acertos, 0)) hits,
            SUM(questoes) FILTER (WHERE nota IS NOT NULL AND questoes > 0) questions,
            SUM(COALESCE(nota, 0)) sum_nota,
            COUNT(nota) count_nota
            FROM attempts''', [names])
        k = cur.fetchone()
        data['kpis'].update(total_alunos=k['students'] or 0, total_simulados=k['expected_exams'] or 0,
            simulados_respondidos=k['exams'] or 0,
            simulados_nao_respondidos=(k['expected_exams'] or 0)-(k['exams'] or 0),
            media_geral=round(float(k['sum_nota'])/k['count_nota'], 1) if k['count_nota'] else 0,
            participacao=round(100*(k['completed'] or 0)/k['students'], 1) if k['students'] else 0,
            questoes_respondidas=k['questions'] or 0)

        cur.execute(sql + '''SELECT school_key, student_key, MAX(nome) nome, MAX(ra) ra,
            MAX(serie) serie, MAX(nivel_serie) nivel_serie, MAX(turma) turma, COUNT(*) previstos,
            COUNT(*) FILTER (WHERE nota IS NOT NULL AND questoes > 0) simulados,
            SUM(COALESCE(acertos, 0)) acertos,
            SUM(questoes) FILTER (WHERE nota IS NOT NULL AND questoes > 0) questoes,
            SUM(COALESCE(nota, 0)) sum_nota,
            COUNT(nota) count_nota
            FROM attempts GROUP BY 1,2''', [names])
        students = cur.fetchall()
        for r in students:
            r['taxa_acerto'] = round(float(r['sum_nota'])/r['count_nota'], 1) if r['count_nota'] else None
        evaluated = [r for r in students if r['taxa_acerto'] is not None]
        # Priorizar alunos com dados expressivos (ao menos 2 simulados ou 35+ questoes)
        robust = [r for r in evaluated if r['simulados'] >= 2 or (r['questoes'] or 0) >= 35]
        if len(robust) >= 10:
            ranked_students = robust
            data['criterio_minimo_questoes'] = 35
        else:
            eligible = [r for r in evaluated if (r['questoes'] or 0) >= 20]
            ranked_students = eligible if len(eligible) >= 10 else evaluated
            data['criterio_minimo_questoes'] = 20 if eligible else 0
        data['melhores_alunos'] = sorted(ranked_students, key=lambda r: (-r['taxa_acerto'], -r['questoes'], -r['simulados'], r['nome'] or ''))
        data['alunos_atencao'] = sorted(ranked_students, key=lambda r: (r['taxa_acerto'], -r['questoes'], -r['simulados'], r['nome'] or ''))
        data['total_alunos_pendentes'] = sum(not r['simulados'] for r in students)
        data['alunos_pendentes'] = [{'nome': r['nome'], 'escola': r['school_key'],
            'school_key': r['school_key'], 'student_key': r['student_key'],
            'serie': r['nivel_serie'] or r['serie'],
            'nivel_serie': r['nivel_serie'] or r['serie'],
            'turma': r['turma'], 'simulados_previstos': r['previstos']}
            for r in sorted(students, key=lambda r: (-r['previstos'], r['nome'] or '')) if not r['simulados']][:20]

        cur.execute(sql + '''SELECT bimestre,
            COUNT(DISTINCT (school_key, student_key)) expected,
            COUNT(DISTINCT (school_key, student_key)) FILTER (WHERE nota IS NOT NULL AND questoes > 0) completed,
            COUNT(*) FILTER (WHERE nota IS NOT NULL AND questoes > 0) exams,
            SUM(COALESCE(acertos, 0)) hits,
            SUM(questoes) FILTER (WHERE nota IS NOT NULL AND questoes > 0) questions,
            SUM(COALESCE(nota, 0)) sum_nota, COUNT(nota) count_nota
            FROM attempts WHERE bimestre IS NOT NULL GROUP BY 1 ORDER BY 1''', [names])
        data['evolucao_bimestre'] = [{'bimestre': r['bimestre'], 'esperados': r['expected'],
            'fizeram': r['completed'], 'simulados': r['exams'],
            'taxa_acerto': round(float(r['sum_nota'])/r['count_nota'], 1) if r['count_nota'] else None}
            for r in cur.fetchall()]

        cur.execute(sql + '''SELECT nivel_serie,
            COUNT(DISTINCT (school_key, student_key)) expected,
            COUNT(DISTINCT (school_key, student_key)) FILTER (WHERE nota IS NOT NULL AND questoes > 0) completed,
            SUM(COALESCE(acertos, 0)) hits,
            SUM(questoes) FILTER (WHERE nota IS NOT NULL AND questoes > 0) questions,
            SUM(COALESCE(nota, 0)) sum_nota, COUNT(nota) count_nota
            FROM attempts WHERE nivel_serie IS NOT NULL GROUP BY 1''', [names])
        series_order = [
            '1F ( 1ª Série )', '1F ( 2ª Série )', '1F ( 3ª Série )', '1F ( 4ª Série )', '1F ( 5ª Série )',
            '2F ( 6ª Série )', '2F ( 7ª Série )', '2F ( 8ª Série )', '2F ( 9ª Série )',
            'E.M ( 1º Ano )', 'E.M ( 2º Ano )', 'E.M ( 3º Ano )'
        ]
        series_rows = cur.fetchall()
        series_rows.sort(key=lambda r: series_order.index(r['nivel_serie']) if r['nivel_serie'] in series_order else 999)
        data['por_serie'] = [{'serie': r['nivel_serie'], 'nivel_serie': r['nivel_serie'],
            'esperados': r['expected'], 'fizeram': r['completed'],
            'participacao': round(100.0 * float(r['completed']) / float(r['expected']), 1) if r['expected'] else 0,
            'taxa_acerto': round(float(r['sum_nota']) / float(r['count_nota']), 1) if r['count_nota'] else None}
            for r in series_rows]

        cur.execute(sql + '''SELECT school_key,
            MAX(COALESCE(nivel_serie, serie, 'Não informada')) serie,
            turma,
            COUNT(DISTINCT (school_key, student_key)) expected,
            COUNT(DISTINCT (school_key, student_key)) FILTER (WHERE nota IS NOT NULL AND questoes > 0) completed,
            COUNT(DISTINCT id_simulado) simulados,
            SUM(COALESCE(acertos, 0)) hits,
            SUM(questoes) FILTER (WHERE nota IS NOT NULL AND questoes > 0) questions,
            SUM(COALESCE(nota, 0)) sum_nota, COUNT(nota) count_nota
            FROM attempts
            WHERE turma IS NOT NULL AND TRIM(turma) <> ''
            GROUP BY 1, 3
            ORDER BY 1, 2, 3''', [names])
        classes_rows = []
        for r in cur.fetchall():
            school = school_map.get(r['school_key'])
            esc_name = school['escola'] if school else r['school_key']
            classes_rows.append({
                'escola': esc_name,
                'serie': r['serie'],
                'turma': r['turma'],
                'esperados': r['expected'],
                'fizeram': r['completed'],
                'simulados': r['simulados'],
                'taxa_acerto': round(float(r['sum_nota']) / float(r['count_nota']), 1) if r['count_nota'] else None
            })
        data['por_turma'] = classes_rows
        data['analise_bimestral'] = _build_bimonthly_analysis(
            cur, names, school_map, selected, own, peers, catalog, data['bimestres_disponiveis']
        )

        cur.execute(sql + '''SELECT school_key, COUNT(DISTINCT student_key) expected,
            COUNT(DISTINCT student_key) FILTER (WHERE nota IS NOT NULL AND questoes > 0) completed,
            SUM(COALESCE(acertos, 0)) hits,
            SUM(questoes) FILTER (WHERE nota IS NOT NULL AND questoes > 0) questions,
            SUM(COALESCE(nota, 0)) sum_nota, COUNT(nota) count_nota
            FROM attempts GROUP BY 1''', [names])
        summaries = []
        for r in cur.fetchall():
            school = school_map[r['school_key']]
            summaries.append({'escola': school['escola'], 'uniao': school['uniao'],
                'associacao': school['associacao'], 'esperados': r['expected'], 'fizeram': r['completed'],
                'participacao': round(100*r['completed']/r['expected'], 1) if r['expected'] else 0,
                'taxa_acerto': round(float(r['sum_nota'])/r['count_nota'], 1) if r['count_nota'] else None})
        present = {r['escola'] for r in summaries}
        summaries.extend({'escola': school['escola'], 'uniao': school['uniao'],
            'associacao': school['associacao'], 'esperados': 0, 'fizeram': 0,
            'participacao': 0, 'taxa_acerto': None} for school in selected if school['escola'] not in present)
        data['escolas_resumo'] = sorted(summaries, key=lambda r: (r['esperados'] == 0, r['participacao'], r['escola']))

        # Peers were already calculated at the top

        cur.execute(sql + '''SELECT school_key,
            COUNT(*) expected,
            COUNT(*) FILTER (WHERE nota IS NOT NULL AND questoes > 0) completed,
            COUNT(DISTINCT student_key) FILTER (WHERE nota IS NOT NULL AND questoes > 0) students,
            SUM(COALESCE(acertos, 0)) hits,
            SUM(questoes) FILTER (WHERE nota IS NOT NULL AND questoes > 0) questions,
            SUM(COALESCE(nota, 0)) sum_nota, COUNT(nota) count_nota
            FROM attempts GROUP BY 1''', [peer_names])
        peer_stats = {r['school_key']: r for r in cur.fetchall()}
        ranked = []
        for r in peers:
            stat = peer_stats.get(r['escola'].strip().lower())
            ranked.append(dict(r, students=(stat['students'] or 0) if stat else 0,
                               expected=(stat['expected'] or 0) if stat else 0,
                               completed=(stat['completed'] or 0) if stat else 0,
                               hits=(stat['hits'] or 0) if stat else 0,
                               questions=(stat['questions'] or 0) if stat else 0,
                               sum_nota=float(stat.get('sum_nota', 0) or 0) if stat else 0,
                               count_nota=(stat.get('count_nota', 0) or 0) if stat else 0))
        data['rankings'] = {}

        is_master = scope.get('hierarquia') in ('Master', 'Administrador')

        if vision == 'uniao':
            # 1. Posição da União entre todas elas (com as outras uniões inibidas sem aparecer o nome)
            data['rankings']['uniao'] = _build_ranking(
                ranked,
                group_key_func=lambda r: r['uniao'],
                name_key='uniao',
                own_check_func=lambda k, r: r['uniao'] == target_uniao,
                mask_others=not is_master
            )
            # 2. Rank de Associações que fazem parte dessa união apenas (todas reveladas)
            assoc_rows = [r for r in ranked if r['uniao'] == target_uniao]
            data['rankings']['associacao'] = _build_ranking(
                assoc_rows,
                group_key_func=lambda r: (r['uniao'], r['associacao']),
                name_key='associacao',
                own_check_func=lambda k, r: True,
                mask_others=False
            )
            # 3. Rank de Escolas da união (apenas as escolas das associações dessa união)
            escola_rows = [r for r in ranked if r['uniao'] == target_uniao]
            data['rankings']['escola'] = _build_ranking(
                escola_rows,
                group_key_func=lambda r: r['id_escolas'],
                name_key='escola',
                own_check_func=lambda k, r: True,
                mask_others=False
            )

        elif vision == 'associacao':
            if is_master:
                data['rankings']['uniao'] = _build_ranking(
                    ranked,
                    group_key_func=lambda r: r['uniao'],
                    name_key='uniao',
                    own_check_func=lambda k, r: r['uniao'] == target_uniao,
                    mask_others=False
                )
            
            # 1. Posição dessa associação específica entre as associações da própria união que ela faz parte (outras inibidas)
            assoc_rows = [r for r in ranked if r['uniao'] == target_uniao] if target_uniao else ranked
            data['rankings']['associacao'] = _build_ranking(
                assoc_rows,
                group_key_func=lambda r: (r['uniao'], r['associacao']),
                name_key='associacao',
                own_check_func=lambda k, r: r['associacao'] == target_assoc,
                mask_others=not is_master
            )
            # 2. Rank das escolas apenas das escolas que são dessa associação (todas reveladas)
            escola_rows = [r for r in ranked if (not target_uniao or r['uniao'] == target_uniao) and r['associacao'] == target_assoc]
            data['rankings']['escola'] = _build_ranking(
                escola_rows,
                group_key_func=lambda r: r['id_escolas'],
                name_key='escola',
                own_check_func=lambda k, r: True,
                mask_others=False
            )

        elif vision == 'escola':
            # Não vai aparecer rank da união nem de associação!
            # Apenas o rank dela entre as outras escolas da associação (outras escolas inibidas)
            escola_rows = [r for r in ranked if (not target_uniao or r['uniao'] == target_uniao) and (not target_assoc or r['associacao'] == target_assoc)]
            data['rankings']['escola'] = _build_ranking(
                escola_rows,
                group_key_func=lambda r: r['id_escolas'],
                name_key='escola',
                own_check_func=lambda k, r: str(r['id_escolas']) == str(target_escola),
                mask_others=not is_master
            )

        else:
            # Visão Master geral (sem filtros de recorte): exibe ranking completo e aberto da rede
            data['rankings']['uniao'] = _build_ranking(
                ranked,
                group_key_func=lambda r: r['uniao'],
                name_key='uniao',
                own_check_func=lambda k, r: True,
                mask_others=False
            )
            data['rankings']['associacao'] = _build_ranking(
                ranked,
                group_key_func=lambda r: (r['uniao'], r['associacao']),
                name_key='associacao',
                own_check_func=lambda k, r: True,
                mask_others=False
            )
            data['rankings']['escola'] = _build_ranking(
                ranked,
                group_key_func=lambda r: r['id_escolas'],
                name_key='escola',
                own_check_func=lambda k, r: True,
                mask_others=False
            )

        # Evaluated answers only; direct database pass on gabarito_aluno using school and period indexes
        g_period = period.replace('a.', 'g.') if period else 'TRUE'
        cur.execute(f'''
        SELECT GROUPING(g.disciplina) difficulty_group, GROUPING(g.dificuldade) discipline_group,
          g.disciplina, g.dificuldade,
          COUNT(*) FILTER (WHERE g.status_questao='ACERTO') hits,
          COUNT(*) FILTER (WHERE g.status_questao='ERRO') misses
        FROM pluraal.gabarito_aluno g
        WHERE LOWER(TRIM(g.escola)) = ANY(%s)
          AND {g_period}
          AND g.status_questao IN ('ACERTO','ERRO')
        GROUP BY GROUPING SETS ((g.disciplina),(g.dificuldade),(g.disciplina,g.dificuldade))''', [names] + period_values)
        subject_rows, difficulty_rows, matrix_rows = [], [], []
        for r in cur.fetchall():
            count = r['hits'] + r['misses']
            if not count:
                continue
            value = {'acertos': r['hits'], 'erros': r['misses']}
            if r['difficulty_group']:
                difficulty_rows.append(dict(value, dificuldade=r['dificuldade']))
            elif r['discipline_group']:
                subject_rows.append(dict(value, disciplina=r['disciplina']))
            else:
                matrix_rows.append(dict(value, disciplina=r['disciplina'], dificuldade=r['dificuldade']))
        data['por_disciplina'] = _combine_answer_rows(subject_rows, ('disciplina',))
        data['por_dificuldade'] = _combine_answer_rows(difficulty_rows, ('dificuldade',))
        data['matriz_disciplina_dificuldade'] = _combine_answer_rows(
            matrix_rows, ('disciplina', 'dificuldade'))
        data['habilidades_por_nivel'] = _institution_skills(cur, selected, period, period_values)
        
        cur.execute('''
            SELECT DISTINCT id_simulado, school_key,
                   MAX(nome_simulado) as nome_simulado,
                   MAX(bimestre) as bimestre,
                   MAX(ano) as ano,
                   COUNT(student_key) as alunos,
                   COUNT(student_key) FILTER (WHERE nota IS NOT NULL AND questoes > 0) as fizeram
            FROM tmp_attempts_report
            GROUP BY 1, 2
        ''')
        simulados_dict = {}
        for r in cur.fetchall():
            sinfo = school_map.get(r['school_key'])
            if sinfo:
                uniao = sinfo.get('uniao', '')
                key = (r['id_simulado'], uniao)
                
                raw_nome = r['nome_simulado'] or r['id_simulado']
                clean_nome = re.sub(r' - [A-Za-z0-9]+ - .*? - Alunos.*$', '', raw_nome, flags=re.IGNORECASE)

                if key not in simulados_dict:
                    simulados_dict[key] = {
                        'id_simulado': r['id_simulado'],
                        'nome_simulado': clean_nome,
                        'bimestre': r['bimestre'],
                        'ano': r['ano'],
                        'uniao': uniao,
                        'id_uniao': sinfo.get('id_unioes', ''),
                        'alunos': 0,
                        'fizeram': 0
                    }
                simulados_dict[key]['alunos'] += r['alunos']
                simulados_dict[key]['fizeram'] += r['fizeram']
                
        data['simulados_disponiveis'] = list(simulados_dict.values())
        
        _REPORT_CACHE[cache_key] = (now, data)
        return data


def get_student_detail(user_id, school_key, student_key, filters=None):
    filters = filters or {}
    student_key = _student_key(student_key, '')
    with get_db_cursor(commit=False) as cur:
        scope = get_effective_user_scope(user_id, cur, allow_simulation=True)
        catalog = _catalog(cur)
        own, _, _ = _scope_rows(catalog, scope, filters)
        if school_key not in {r['escola'].strip().lower() for r in own}:
            raise PermissionError('Aluno fora do seu escopo')
        period, values = _period(filters)
        sql = _attempts(period)
        cur.execute(sql + '''SELECT MAX(nome) nome, MAX(ra) ra, MAX(serie) serie, MAX(nivel_serie) nivel_serie, MAX(turma) turma,
            COUNT(*) simulados_previstos,
            COUNT(*) FILTER (WHERE nota IS NULL OR questoes IS NULL OR questoes=0) simulados_pendentes,
            COUNT(*) FILTER (WHERE nota IS NOT NULL AND questoes > 0) simulados,
            SUM(questoes) FILTER (WHERE nota IS NOT NULL AND questoes > 0) questoes,
            SUM(COALESCE(acertos, 0)) acertos,
            SUM(COALESCE(nota, 0)) sum_nota, COUNT(nota) count_nota,
            ARRAY_AGG(id_simulado) FILTER (WHERE nota IS NOT NULL AND questoes > 0) ids
            FROM attempts WHERE school_key=%s AND student_key=%s''', [[school_key], *values, school_key, student_key])
        row = cur.fetchone()
        if not row or not row['nome']:
            raise LookupError('Aluno não encontrado')
        row['serie'] = row['nivel_serie'] or row['serie']
        ids = row.pop('ids') or []
        row['taxa_acerto'] = round(float(row['sum_nota'])/row['count_nota'], 1) if row['count_nota'] else None
        cur.execute(sql + '''SELECT id_simulado, nome_simulado, bimestre, inicio, nota, questoes, acertos
            FROM attempts WHERE school_key=%s AND student_key=%s
            ORDER BY inicio DESC NULLS LAST, id_simulado DESC''', [[school_key], *values, school_key, student_key])
        row['historico'] = [{'id_simulado': a['id_simulado'], 'nome': a['nome_simulado'],
            'bimestre': a['bimestre'], 'data': a['inicio'].isoformat() if a['inicio'] else None,
            'realizado': a['nota'] is not None and bool(a['questoes']), 'questoes': a['questoes'],
            'acertos': a['acertos'],
            'taxa_acerto': round(float(a['nota']), 1) if a['nota'] is not None and a['questoes'] else None}
            for a in cur.fetchall()]
        row.update(disciplinas=[], dificuldades=[], habilidades=[], habilidades_mais_acertadas=[], habilidades_mais_erradas=[],
                   questoes_detalhadas=0, simulados_com_detalhamento=0, simulados_sem_detalhamento=0)
        if not ids:
            return row
        common = f'''FROM pluraal.gabarito_aluno g WHERE LOWER(TRIM(g.escola))=%s
            AND {_student_identity('g')}=%s AND g.id_simulado=ANY(%s)
            AND g.status_questao IN ('ACERTO','ERRO')'''
        args = [school_key, student_key, ids]
        cur.execute('SELECT g.id_simulado, COUNT(*) questoes ' + common + ' GROUP BY 1', args)
        details = {r['id_simulado']: r['questoes'] for r in cur.fetchall()}
        row['questoes_detalhadas'] = sum(details.values())
        row['simulados_com_detalhamento'] = len(details)
        missing_ids = [exam_id for exam_id in ids if exam_id not in details]
        row['simulados_sem_detalhamento'] = len(missing_ids)
        for exam in row['historico']:
            exam['questoes_detalhadas'] = details.get(exam['id_simulado'], 0)
        cur.execute("SELECT g.disciplina, COUNT(*) FILTER (WHERE g.status_questao='ACERTO') acertos, COUNT(*) FILTER (WHERE g.status_questao='ERRO') erros " + common + ' GROUP BY 1 ORDER BY 2+3 DESC', args)
        discipline_rows = cur.fetchall()
        if missing_ids:
            # A completed exam can have a consolidated score before its answer
            # details are imported. Retain that subject result without inventing skills/difficulty.
            cur.execute(f'''SELECT a.id_simulado, a.disciplina,
                COALESCE(MAX(a.total_acertos), MAX(a.qtd_acertos_disciplina)) acertos,
                COALESCE(MAX(a.total_questao), MAX(a.qtd_questao_disciplina)) questoes
                FROM pluraal.aluno a WHERE LOWER(TRIM(a.escola))=%s
                  AND {_student_identity('a')}=%s AND a.id_simulado=ANY(%s)
                  AND (a.total_final IS NOT NULL OR a.nota_disciplina IS NOT NULL)
                  AND COALESCE(a.total_questao, a.qtd_questao_disciplina, 0) > 0 AND {period}
                  AND LOWER(TRIM(COALESCE(a.disciplina,''))) NOT IN ('total', 'total ()', 'total geral')
                GROUP BY 1,2''', [school_key, student_key, missing_ids, *values])
            discipline_rows.extend({'disciplina': r['disciplina'], 'acertos': r['acertos'] or 0,
                                     'erros': r['questoes'] - (r['acertos'] or 0)}
                                   for r in cur.fetchall())
        row['disciplinas'] = _combine_answer_rows(discipline_rows, ('disciplina',))
        cur.execute("SELECT g.dificuldade, COUNT(*) FILTER (WHERE g.status_questao='ACERTO') acertos, COUNT(*) FILTER (WHERE g.status_questao='ERRO') erros " + common + ' GROUP BY 1', args)
        row['dificuldades'] = _combine_answer_rows(cur.fetchall(), ('dificuldade',))
        cur.execute(f"SELECT {_subject_sql('g')} disciplina, {_skill_sql('g')} habilidade, MAX(NULLIF(TRIM(g.descricao),'')) descricao, COUNT(*) FILTER (WHERE g.status_questao='ACERTO') acertos, COUNT(*) FILTER (WHERE g.status_questao='ERRO') erros, COUNT(DISTINCT g.id_simulado) simulados " + common + " AND (NULLIF(TRIM(g.habilidade),'') IS NOT NULL OR TRIM(COALESCE(g.descricao,'')) ~* '^[0-9]+[A-Z][0-9]+[[:space:]]*[-–:]') GROUP BY 1,2", args)
        skills = [_format_skill(r) for r in cur.fetchall()]
        row['habilidades'] = sorted(skills, key=lambda r: (r['taxa_acerto'], -r['questoes'], r['disciplina'], r['habilidade']))
        row['habilidades_mais_acertadas'] = sorted(
            (r for r in skills if r['acertos']), key=lambda r: (-r['acertos'], r['erros']))[:5]
        row['habilidades_mais_erradas'] = sorted(
            (r for r in skills if r['erros']), key=lambda r: (-r['erros'], r['acertos']))[:5]
        return row


def get_pending_students(user_id, filters=None, page=1, search='', pending_only=True):
    filters = filters or {}
    page = max(1, int(page))
    with get_db_cursor(commit=False) as cur:
        scope = get_effective_user_scope(user_id, cur, allow_simulation=True)
        catalog = _catalog(cur)
        _, selected, _ = _scope_rows(catalog, scope, filters)
        if not selected:
            return {'alunos': [], 'total': 0, 'pagina': page, 'por_pagina': 20}
        names = [r['escola'].strip().lower() for r in selected]
        period, values = _period(filters)
        cur.execute(_attempts(period) + ''' , students AS (
            SELECT school_key, student_key, MAX(nome) nome, MAX(serie) serie,
                MAX(nivel_serie) nivel_serie,
                MAX(turma) turma, COUNT(*) previstos,
                COUNT(*) FILTER (WHERE nota IS NOT NULL AND questoes > 0) feitos,
                SUM(COALESCE(acertos, 0)) acertos,
                SUM(questoes) FILTER (WHERE nota IS NOT NULL AND questoes > 0) questoes,
                SUM(COALESCE(nota, 0)) sum_nota, COUNT(nota) count_nota
            FROM attempts GROUP BY 1,2
        )
        SELECT school_key, student_key, nome, serie, nivel_serie, turma, previstos, feitos, acertos, questoes, sum_nota, count_nota,
               COUNT(*) OVER() total
        FROM students WHERE (%s=FALSE OR feitos=0) AND (nome ILIKE %s OR student_key ILIKE %s)
        ORDER BY feitos DESC, previstos DESC, nome, school_key, student_key
        LIMIT 20 OFFSET %s''', [names, *values, pending_only,
                              '%' + search.strip() + '%', '%' + search.strip() + '%', (page-1)*20])
        rows = cur.fetchall()
        return {'alunos': [{'school_key': r['school_key'], 'student_key': r['student_key'],
                           'escola': r['school_key'], 'nome': r['nome'],
                           'serie': r['nivel_serie'] or r['serie'],
                           'nivel_serie': r['nivel_serie'] or r['serie'],
                           'turma': r['turma'], 'simulados_previstos': r['previstos'],
                           'simulados': r['feitos'], 'questoes': r['questoes'] or 0,
                           'taxa_acerto': round(float(r['sum_nota'] or 0) / float(r['count_nota']), 1) if r['count_nota'] else None}
                          for r in rows],
                'total': rows[0]['total'] if rows else 0,
                'pagina': page, 'por_pagina': 20}


def get_class_report_students(user_id, school_key, serie=None, turma=None, filters=None):
    filters = filters or {}
    period, period_values = _period(filters)
    sql = _attempts(period)
    with get_db_cursor(commit=False) as cur:
        extra_clauses = []
        extra_vals = []
        if serie:
            extra_clauses.append("(COALESCE(a.nivel_serie, a.serie) = %s OR a.serie = %s)")
            extra_vals.extend([serie, serie])
        if turma:
            extra_clauses.append("a.turma = %s")
            extra_vals.append(turma)
        clause_str = (" AND " + " AND ".join(extra_clauses)) if extra_clauses else ""

        cur.execute(sql + f'''SELECT school_key, student_key, MAX(nome) nome, MAX(ra) ra,
            MAX(serie) serie, MAX(nivel_serie) nivel_serie, MAX(turma) turma,
            COUNT(*) FILTER (WHERE nota IS NOT NULL AND questoes > 0) simulados,
            SUM(COALESCE(acertos, 0)) acertos,
            SUM(questoes) FILTER (WHERE nota IS NOT NULL AND questoes > 0) questoes,
            SUM(COALESCE(nota, 0)) sum_nota, COUNT(nota) count_nota
            FROM attempts
            WHERE school_key = %s {clause_str}
            GROUP BY 1,2''', [[school_key], *period_values, school_key, *extra_vals])
        students = cur.fetchall()
        for r in students:
            r['taxa_acerto'] = round(float(r['sum_nota']) / float(r['count_nota']), 1) if r['count_nota'] else None
        return students

def get_simulado_detail(user_id, simulado_id, filters=None):
    filters = filters or {}
    with get_db_cursor(commit=False) as cur:
        scope = get_effective_user_scope(user_id, cur, allow_simulation=True)
        catalog = _catalog(cur)
        own, selected, preview = _scope_rows(catalog, scope, filters)
        target = selected if selected else own
        names = [r['escola'].strip().lower() for r in target]
        if not names:
            return {'alunos': [], 'unidades': []}
            
        school_map = {r['escola'].strip().lower(): r for r in target}
        period, values = _period(filters)
        sql = _attempts(period)
        
        cur.execute(sql + '''SELECT school_key, MAX(nome) as nome, MAX(serie) as serie, MAX(nivel_serie) as nivel_serie, MAX(turma) as turma, MAX(nota) as nota, MAX(acertos) as acertos, MAX(questoes) as questoes
            FROM attempts WHERE school_key = ANY(%s) AND id_simulado = %s
            GROUP BY student_key, school_key
            ORDER BY MAX(nome)''', [names] + values + [names, simulado_id])
            
        alunos_list = []
        for r in cur.fetchall():
            sinfo = school_map.get(r['school_key'])
            alunos_list.append({
                'nome': r['nome'],
                'escola': sinfo['escola'] if sinfo else r['school_key'],
                'turma': r['turma'],
                'serie': r['nivel_serie'] or r['serie'],
                'nota': r['nota'],
                'acertos': r['acertos'],
                'questoes': r['questoes']
            })
            
        cur.execute(sql + '''SELECT school_key,
            COUNT(student_key) as alunos,
            COUNT(student_key) FILTER (WHERE nota IS NOT NULL AND questoes > 0) as fizeram,
            SUM(nota) as sum_nota, COUNT(nota) as count_nota
        FROM attempts WHERE school_key = ANY(%s) AND id_simulado = %s
        GROUP BY school_key
        ORDER BY MAX(school_key)''', [names] + values + [names, simulado_id])
        
        attempt_stats = {r['school_key']: r for r in cur.fetchall()}
        
        unidades = []
        for sinfo in target:
            school_key = sinfo['escola'].strip().lower()
            r = attempt_stats.get(school_key)
            if r:
                alunos = r['alunos']
                fizeram = r['fizeram']
                media = round(float(r['sum_nota'])/r['count_nota'], 1) if r['count_nota'] else None
            else:
                alunos = 0
                fizeram = 0
                media = None
                
            unidades.append({
                'uniao': sinfo.get('uniao', ''),
                'associacao': sinfo.get('associacao', ''),
                'escola': sinfo['escola'],
                'alunos': alunos,
                'fizeram': fizeram,
                'media': media
            })
                
        return {'alunos': alunos_list, 'unidades': unidades}
