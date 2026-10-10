def get_simulado_detail(user_id, simulado_id, filters=None):
    filters = filters or {}
    with get_db_cursor(commit=False) as cur:
        from Backend.services.report_service import _catalog, _scope_rows, _period, _attempts, get_effective_user_scope
        scope = get_effective_user_scope(user_id, cur)
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
            
        alunos = []
        for r in cur.fetchall():
            sinfo = school_map.get(r['school_key'])
            alunos.append({
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
        ORDER BY MAX(nome)''', [names] + values + [names, simulado_id])
        
        unidades = []
        for r in cur.fetchall():
            sinfo = school_map.get(r['school_key'])
            if sinfo:
                unidades.append({
                    'uniao': sinfo.get('uniao', ''),
                    'associacao': sinfo.get('associacao', ''),
                    'escola': sinfo['escola'],
                    'alunos': r['alunos'],
                    'fizeram': r['fizeram'],
                    'media': round(float(r['sum_nota'])/r['count_nota'], 1) if r['count_nota'] else None
                })
                
        return {'alunos': alunos, 'unidades': unidades}
