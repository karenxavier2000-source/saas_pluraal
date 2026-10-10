import re

with open('Backend/services/report_service.py', 'r', encoding='utf-8') as f:
    code = f.read()

# For Associações
code = code.replace(
    "{'associacao': a, 'uniao': u, 'bimestres': {}, 'hits': 0.0, 'questions': 0.0, 'fizeram': 0, 'alunos': 0}",
    "{'associacao': a, 'uniao': u, 'bimestres': {}, 'hits': 0.0, 'questions': 0.0, 'sum_nota': 0.0, 'count_nota': 0, 'fizeram': 0, 'alunos': 0}"
)
code = code.replace(
    "{'hits': 0.0, 'questions': 0.0, 'fizeram': 0, 'alunos': 0, 'simulados': 0}",
    "{'hits': 0.0, 'questions': 0.0, 'sum_nota': 0.0, 'count_nota': 0, 'fizeram': 0, 'alunos': 0, 'simulados': 0}"
)

# Replace the aggregation code
# Find the block for Associações
code = code.replace(
    "ab['questions'] += q_val\n            ab['fizeram'] += (r['completed'] or 0)",
    "ab['questions'] += q_val\n            ab['sum_nota'] += float(r['sum_nota'] or 0)\n            ab['count_nota'] += (r['count_nota'] or 0)\n            ab['fizeram'] += (r['completed'] or 0)"
)
code = code.replace(
    "a_entry['questions'] += q_val\n            a_entry['fizeram'] += (r['completed'] or 0)",
    "a_entry['questions'] += q_val\n            a_entry['sum_nota'] += float(r['sum_nota'] or 0)\n            a_entry['count_nota'] += (r['count_nota'] or 0)\n            a_entry['fizeram'] += (r['completed'] or 0)"
)

code = code.replace(
    "if bd and bd['questions']:\n                    t = round(100.0 * bd['hits'] / bd['questions'], 1)",
    "if bd and bd['count_nota']:\n                    t = round(bd['sum_nota'] / bd['count_nota'], 1)"
)
code = code.replace(
    "media_geral = round(100.0 * a_data['hits'] / a_data['questions'], 1) if a_data['questions'] else 0",
    "media_geral = round(a_data['sum_nota'] / a_data['count_nota'], 1) if a_data['count_nota'] else 0"
)

# For Escolas
code = code.replace(
    "{'escola': esc, 'uniao': u, 'associacao': a, 'bimestres': {}, 'hits': 0.0, 'questions': 0.0, 'fizeram': 0, 'alunos': 0}",
    "{'escola': esc, 'uniao': u, 'associacao': a, 'bimestres': {}, 'hits': 0.0, 'questions': 0.0, 'sum_nota': 0.0, 'count_nota': 0, 'fizeram': 0, 'alunos': 0}"
)
code = code.replace(
    "eb['questions'] += q_val\n            eb['fizeram'] += (r['completed'] or 0)",
    "eb['questions'] += q_val\n            eb['sum_nota'] += float(r['sum_nota'] or 0)\n            eb['count_nota'] += (r['count_nota'] or 0)\n            eb['fizeram'] += (r['completed'] or 0)"
)
code = code.replace(
    "e_entry['questions'] += q_val\n            e_entry['fizeram'] += (r['completed'] or 0)",
    "e_entry['questions'] += q_val\n            e_entry['sum_nota'] += float(r['sum_nota'] or 0)\n            e_entry['count_nota'] += (r['count_nota'] or 0)\n            e_entry['fizeram'] += (r['completed'] or 0)"
)

code = code.replace(
    "media_geral = round(100.0 * e_data['hits'] / e_data['questions'], 1) if e_data['questions'] else 0",
    "media_geral = round(e_data['sum_nota'] / e_data['count_nota'], 1) if e_data['count_nota'] else 0"
)

# For Alunos
code = code.replace(
    "al_entry = aluno_map.setdefault(stu, {'nome': r['nome'], 'escola': esc, 'serie': r['serie'], 'turma': r['turma'], 'bimestres': {}, 'hits': 0.0, 'questions': 0.0, 'fizeram': 0, 'simulados': 0})",
    "al_entry = aluno_map.setdefault(stu, {'nome': r['nome'], 'escola': esc, 'serie': r['serie'], 'turma': r['turma'], 'bimestres': {}, 'hits': 0.0, 'questions': 0.0, 'sum_nota': 0.0, 'count_nota': 0, 'fizeram': 0, 'simulados': 0})"
)
code = code.replace(
    "alb['questions'] += q_val\n            alb['fizeram'] += (r['completed'] or 0)",
    "alb['questions'] += q_val\n            alb['sum_nota'] += float(r['sum_nota'] or 0)\n            alb['count_nota'] += (r['count_nota'] or 0)\n            alb['fizeram'] += (r['completed'] or 0)"
)
code = code.replace(
    "al_entry['questions'] += q_val\n            al_entry['fizeram'] += (r['completed'] or 0)",
    "al_entry['questions'] += q_val\n            al_entry['sum_nota'] += float(r['sum_nota'] or 0)\n            al_entry['count_nota'] += (r['count_nota'] or 0)\n            al_entry['fizeram'] += (r['completed'] or 0)"
)

code = code.replace(
    "media_geral = round(100.0 * al_data['hits'] / al_data['questions'], 1) if al_data['questions'] else 0",
    "media_geral = round(al_data['sum_nota'] / al_data['count_nota'], 1) if al_data['count_nota'] else 0"
)

with open('Backend/services/report_service.py', 'w', encoding='utf-8') as f:
    f.write(code)

