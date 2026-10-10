"""Scoped PAAEB filter options and dashboard aggregates."""
from flask import Blueprint, g, jsonify, request

from Backend.database.connection import get_db_cursor
from Backend.middleware.auth_middleware import login_required
from Backend.services.delegation_service import get_effective_user_scope
from Backend.services.report_service import _catalog, _scope_rows


paaeb_bp = Blueprint('paaeb', __name__, url_prefix='/api/paaeb')


@paaeb_bp.route('/dashboard', methods=['GET'])
@login_required(required_page='paaeb')
def dashboard():
    filters = {key: request.args.get(key, '').strip() for key in ('uniao', 'associacao', 'escola')}
    requested_series = request.args.get('serie', '').strip()
    try:
        with get_db_cursor() as cur:
            catalog = _catalog(cur)
            scope = get_effective_user_scope(g.current_user['id_usuario'], cur, allow_simulation=True)
            own, selected, _ = _scope_rows(catalog, scope, filters)
            if any(filters.values()) and not selected:
                return jsonify({'message': 'O filtro selecionado está fora do seu acesso.'}), 400

            ids = [row['id_escolas'] for row in selected]
            # Legacy PAAEB union/association codes can differ from the current catalog.
            # School names are unique there; use the catalog ID for scope and its hierarchy.
            # Resolve the verified IAESC name variant so its 3º ano data remains available.
            school_join = '''
                JOIN pluraal.escolas_pluraal e
                  ON LOWER(TRIM(REPLACE(REPLACE(e."ESCOLA", '–', '-'), '  ', ' '))) = CASE
                      WHEN LOWER(TRIM(p.escola)) = LOWER('Instituto Adventista de Ensino de Santa Catarina (IAESC)')
                      THEN LOWER('IAESC - Instituto Adventista de Ensino de Santa Catarina')
                      ELSE LOWER(TRIM(REPLACE(REPLACE(p.escola, '–', '-'), '  ', ' '))) END
            '''
            cur.execute(f'''
                SELECT DISTINCT TRIM(p.serie) AS serie
                FROM "PAAB_PROV".tb_aluno_1 p {school_join}
                WHERE e.id_escolas = ANY(%s) AND NULLIF(TRIM(p.serie), '') IS NOT NULL
                ORDER BY 1
            ''', (ids,))
            series = [row['serie'] for row in cur.fetchall()]
            serie = requested_series if requested_series in series else (
                '5º ano' if '5º ano' in series else (series[0] if series else ''))
            cur.execute(f'''
                SELECT ano, materia,
                       ROUND(AVG(REPLACE(nota, ',', '.')::numeric), 1) AS media
                FROM "PAAB_PROV".tb_media_1 p {school_join}
                WHERE e.id_escolas = ANY(%s)
                  AND TRIM(p.serie) = %s
                  AND nota IS NOT NULL
                  AND REPLACE(TRIM(nota), ',', '.') ~ '^[0-9]+([.][0-9]+)?$'
                GROUP BY ano, materia ORDER BY ano, materia
            ''', (ids, serie))
            history = [{'ano': row['ano'], 'materia': row['materia'],
                        'media': float(row['media'])} for row in cur.fetchall()]

            cur.execute(f'''
                SELECT COUNT(DISTINCT (LOWER(TRIM(p.escola)), LOWER(TRIM(nome_aluno)))) AS alunos
                FROM "PAAB_PROV".tb_aluno_1 p {school_join}
                WHERE e.id_escolas = ANY(%s)
                  AND TRIM(p.serie) = %s
            ''', (ids, serie))
            students = cur.fetchone()['alunos'] or 0

            cur.execute(f'''
                WITH student_scores AS (
                    SELECT ano, p.nome_aluno AS nome,
                           ROUND(AVG(REPLACE(nota, ',', '.')::numeric)
                               FILTER (WHERE materia ILIKE '%%Matem%%'), 1) AS matematica,
                           ROUND(AVG(REPLACE(nota, ',', '.')::numeric)
                               FILTER (WHERE materia ILIKE '%%Portug%%'), 1) AS portugues
                    FROM "PAAB_PROV".tb_aluno_1 p {school_join}
                    WHERE e.id_escolas = ANY(%s)
                      AND TRIM(p.serie) = %s
                      AND REPLACE(TRIM(nota), ',', '.') ~ '^[0-9]+([.][0-9]+)?$'
                    GROUP BY ano, p.nome_aluno
                    HAVING COUNT(DISTINCT materia) >= 2
                ),
                ranked_scores AS (
                    SELECT ano, nome, matematica, portugues,
                           ROW_NUMBER() OVER(PARTITION BY ano ORDER BY nome) as rn
                    FROM student_scores
                )
                SELECT ano, nome, matematica, portugues
                FROM ranked_scores
                WHERE rn <= 150
                ORDER BY ano DESC, nome
            ''', (ids, serie))
            scatter = [{'ano': row['ano'], 'nome': row['nome'], 'matematica': float(row['matematica']),
                        'portugues': float(row['portugues'])} for row in cur.fetchall()
                       if row['matematica'] is not None and row['portugues'] is not None]

            cur.execute(f'''
                SELECT SPLIT_PART(ano, '.', 1) AS ano, materia, nivel_adq, pontos_na_escala, adequacao,
                       MAX(e."ESCOLA") AS example_school,
                       ROUND(AVG(REPLACE(REGEXP_REPLACE(percentual, '[^0-9,.]', '', 'g'), ',', '.')::numeric), 1) AS percentual
                FROM "PAAB_PROV".tb_adequacao_2 p {school_join}
                WHERE e.id_escolas = ANY(%s)
                  AND TRIM(p.serie) = %s
                  AND REPLACE(REGEXP_REPLACE(percentual, '[^0-9,.]', '', 'g'), ',', '.') ~ '^[0-9]+([.][0-9]+)?$'
                GROUP BY SPLIT_PART(ano, '.', 1), materia, nivel_adq, pontos_na_escala, adequacao
                ORDER BY 1, materia, nivel_adq
            ''', (ids, serie))
            levels = [{**row, 'percentual': float(row['percentual'])} for row in cur.fetchall()]

            cur.execute(f'''
                SELECT SPLIT_PART(ano, '.', 1) AS ano, materia, adequacao,
                       ROUND(AVG(REPLACE(REGEXP_REPLACE(percentual_por_ano, '[^0-9,.]', '', 'g'), ',', '.')::numeric), 1) AS percentual
                FROM "PAAB_PROV".tb_adequacao_1 p {school_join}
                WHERE e.id_escolas = ANY(%s)
                  AND TRIM(p.serie) = %s
                  AND REPLACE(REGEXP_REPLACE(percentual_por_ano, '[^0-9,.]', '', 'g'), ',', '.') ~ '^[0-9]+([.][0-9]+)?$'
                GROUP BY SPLIT_PART(ano, '.', 1), materia, adequacao
                ORDER BY 1, materia, adequacao
            ''', (ids, serie))
            adequacy = [{**row, 'percentual': float(row['percentual'])} for row in cur.fetchall()]

            period_tables = (
                ('tb_aluno_1', 'Alunos avaliados'),
                ('tb_adequacao_1', 'Adequação por ano'),
                ('tb_adequacao_2', 'Níveis de adequação'),
                ('tb_media_1', 'Proficiência média'),
                ('tb_dados_gerais_1', 'Dados gerais'),
                ('tb_proficiencia_1', 'Proficiência'),
            )
            periods = []
            for table, label in period_tables:
                cur.execute(f'''
                    SELECT DISTINCT SPLIT_PART(p.ano, '.', 1) AS ano
                    FROM "PAAB_PROV".{table} p {school_join}
                    WHERE e.id_escolas = ANY(%s)
                      AND TRIM(p.serie) = %s
                      AND SPLIT_PART(p.ano, '.', 1) ~ '^[0-9]{{4}}$'
                    ORDER BY 1
                ''', (ids, serie))
                periods.append({'table': table, 'label': label,
                                'years': [row['ano'] for row in cur.fetchall()]})

        return jsonify({'entities': own, 'series': series, 'serie': serie, 'selected_count': len(selected),
                        'students': students, 'history': history, 'levels': levels,
                        'adequacy': adequacy, 'scatter': scatter, 'periods': periods})
    except Exception:
        import logging
        logging.getLogger(__name__).exception('Erro ao consultar PAAEB')
        return jsonify({'message': 'Não foi possível carregar os dados do PAAEB.'}), 500
