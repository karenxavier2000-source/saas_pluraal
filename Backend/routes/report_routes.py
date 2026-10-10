from datetime import datetime
from flask import Blueprint, request, jsonify, g, Response, stream_with_context
from Backend.middleware.auth_middleware import login_required
from Backend.services.report_service import get_reports_data, get_student_detail, get_pending_students, get_class_report_students, clear_report_cache
from Backend.services.data_export_service import get_export_options, prepare_export
from Backend.services.pdf_report_service import (
    generate_network_report_pdf, generate_union_report_pdf, generate_school_report_pdf,
    generate_class_report_pdf, generate_student_report_pdf, generate_comprehensive_report_pdf
)

report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


def _filters():
    return {key: request.args.get(key) for key in (
        'uniao', 'associacao', 'escola', 'ano', 'bimestre',
        'preview_nivel', 'preview_uniao', 'preview_associacao', 'preview_escola')}


@report_bp.route('/pdf/completo', methods=['GET', 'POST'])
@login_required(required_page='reports')
def download_pdf_completo():
    user_id = g.current_user['id_usuario']
    if request.method == 'POST':
        body = request.get_json(silent=True) or {}
        filters = body.get('filters') or body
        tipo_avaliacao = body.get('tipo_avaliacao') or filters.get('tipo_avaliacao', 'simulado')
    else:
        filters = _filters()
        filters.update({key: request.args.get(key) for key in ('serie', 'turma', 'aluno') if request.args.get(key)})
        tipo_avaliacao = request.args.get('tipo_avaliacao', 'simulado')

    try:
        data = get_reports_data(user_id, filters)
        pdf_bytes = generate_comprehensive_report_pdf(data, filters, {'tipo_avaliacao': tipo_avaliacao})
        clean_tipo = str(tipo_avaliacao).lower().replace(' ', '_')
        filename = f"relatorio_executivo_{clean_tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        return Response(pdf_bytes, mimetype='application/pdf', headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Cache-Control': 'no-store',
        })
    except PermissionError as error:
        return jsonify({'message': str(error)}), 403
    except Exception as error:
        import logging
        logging.getLogger(__name__).exception("Erro ao gerar PDF completo")
        return jsonify({'message': f'Não foi possível gerar o PDF: {error}'}), 500


@report_bp.route('/pdf/<report_type>', methods=['GET'])
@login_required(required_page='reports')
def download_pdf(report_type):
    user_id = g.current_user['id_usuario']
    filters = _filters()
    filters.update({key: request.args.get(key) for key in ('serie', 'turma', 'aluno') if request.args.get(key)})
    
    try:
        if report_type in ('completo', 'custom', 'geral'):
            tipo_avaliacao = request.args.get('tipo_avaliacao', 'simulado')
            data = get_reports_data(user_id, filters)
            pdf_bytes = generate_comprehensive_report_pdf(data, filters, {'tipo_avaliacao': tipo_avaliacao})
            clean_tipo = tipo_avaliacao.lower().replace(' ', '_')
            filename = f"relatorio_executivo_{clean_tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        elif report_type == 'rede':
            data = get_reports_data(user_id, filters)
            pdf_bytes = generate_network_report_pdf(data, filters)
            filename = f"relatorio_executivo_rede_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        elif report_type == 'uniao':
            data = get_reports_data(user_id, filters)
            uniao_name = filters.get('uniao')
            if not uniao_name and data.get('entidades_acessiveis'):
                uniao_name = data['entidades_acessiveis'][0].get('uniao')
            pdf_bytes = generate_union_report_pdf(data, uniao_name or "Geral", filters)
            clean_name = (uniao_name or 'geral').lower().replace(' ', '_')
            filename = f"relatorio_executivo_uniao_{clean_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        elif report_type == 'escola':
            data = get_reports_data(user_id, filters)
            school_name = "Rede"
            if data.get('entidades_acessiveis'):
                for e in data['entidades_acessiveis']:
                    if str(e.get('id_escolas')) == str(filters.get('escola')):
                        school_name = e.get('escola')
                        break
                if school_name == "Rede" and len(data['entidades_acessiveis']) == 1:
                    school_name = data['entidades_acessiveis'][0].get('escola')
            pdf_bytes = generate_school_report_pdf(data, school_name, filters)
            filename = f"relatorio_executivo_unidade_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        elif report_type == 'turma':
            school_id = filters.get('escola')
            serie = filters.get('serie')
            turma = filters.get('turma')
            data = get_reports_data(user_id, filters)
            school_name = "Unidade"
            school_key = ""
            for e in data.get('entidades_acessiveis', []):
                if str(e.get('id_escolas')) == str(school_id) or not school_id:
                    school_name = e.get('escola')
                    school_key = e.get('escola').strip().lower()
                    break
            class_students = get_class_report_students(user_id, school_key, serie, turma, filters)
            pdf_bytes = generate_class_report_pdf(school_name, turma or 'Geral', serie or 'Todas', class_students, filters)
            filename = f"relatorio_turma_{turma or 'geral'}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        elif report_type == 'aluno':
            student_key = request.args.get('aluno', '').strip()
            school_key = request.args.get('escola', '').strip().lower()
            if not school_key:
                # Pegar primeira escola disponível do escopo
                data = get_reports_data(user_id, filters)
                if data.get('entidades_acessiveis'):
                    school_key = data['entidades_acessiveis'][0].get('escola', '').strip().lower()
            if not student_key:
                return jsonify({'message': 'Parâmetro aluno é obrigatório para o relatório individual.'}), 400
            student_data = get_student_detail(user_id, school_key, student_key, filters)
            pdf_bytes = generate_student_report_pdf(student_data, filters)
            nome_clean = (student_data.get('nome') or 'aluno')[:15].replace(' ', '_')
            filename = f"boletim_{nome_clean}_{datetime.now().strftime('%Y%m%d')}.pdf"
        else:
            return jsonify({'message': 'Tipo de relatório PDF inválido.'}), 400

        return Response(pdf_bytes, mimetype='application/pdf', headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Cache-Control': 'no-store',
        })
    except PermissionError as error:
        return jsonify({'message': str(error)}), 403
    except Exception as error:
        import logging
        logging.getLogger(__name__).exception("Erro ao gerar PDF")
        return jsonify({'message': f'Não foi possível gerar o PDF: {error}'}), 500


@report_bp.route('/export-options', methods=['GET'])
@login_required()
def export_options():
    # Profile also uses these scoped institution options when Data is disabled.
    return jsonify(get_export_options(g.current_user['id_usuario'])), 200


@report_bp.route('/export/<table>', methods=['GET'])
@login_required(required_page='data')
def export_table(table):
    filters = {key: request.args.get(key) for key in ('uniao', 'associacao', 'escola', 'ano', 'bimestre')}
    try:
        filename, rows = prepare_export(g.current_user['id_usuario'], table, filters)
    except ValueError as error:
        return jsonify({'message': str(error)}), 400
    return Response(stream_with_context(rows), mimetype='text/csv; charset=utf-8', headers={
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
    })


@report_bp.route('', methods=['GET'])
@login_required(required_page='reports')
def reports():
    try:
        user_id = g.current_user['id_usuario']
        if request.args.get('refresh') == '1':
            clear_report_cache(user_id)
        response = jsonify(get_reports_data(user_id, _filters()))
        response.headers['Cache-Control'] = 'no-store'
        return response
    except ValueError as error:
        return jsonify({'error': 'INVALID_FILTER', 'message': str(error)}), 400
    except PermissionError as error:
        return jsonify({'error': 'FORBIDDEN', 'message': str(error)}), 403
    except Exception as error:
        import logging
        logging.getLogger(__name__).exception("Erro ao gerar relatório")
        return jsonify({'error': 'SERVER_ERROR', 'message': f'Não foi possível gerar o relatório: {error}'}), 500


@report_bp.route('/student', methods=['GET'])
@login_required(required_page='reports')
def student():
    school_key = request.args.get('escola', '').strip().lower()
    student_key = request.args.get('aluno', '').strip()
    if not school_key or not student_key:
        return jsonify({'message': 'Aluno e escola são obrigatórios.'}), 400
    try:
        return jsonify(get_student_detail(g.current_user['id_usuario'], school_key, student_key, _filters())), 200
    except PermissionError as error:
        return jsonify({'message': str(error)}), 403
    except LookupError as error:
        return jsonify({'message': str(error)}), 404
    except ValueError as error:
        return jsonify({'message': str(error)}), 400
    except PermissionError as error:
        return jsonify({'message': str(error)}), 403
    except Exception:
        return jsonify({'message': 'Não foi possível carregar o aluno.'}), 500


@report_bp.route('/pending', methods=['GET'])
@login_required(required_page='reports')
def pending():
    try:
        return jsonify(get_pending_students(g.current_user['id_usuario'], _filters(),
                                            request.args.get('pagina', 1),
                                            request.args.get('busca', ''))), 200
    except ValueError as error:
        return jsonify({'message': str(error)}), 400
    except PermissionError as error:
        return jsonify({'message': str(error)}), 403
    except Exception:
        return jsonify({'message': 'Não foi possível carregar os alunos pendentes.'}), 500


@report_bp.route('/students', methods=['GET'])
@login_required(required_page='reports')
def students():
    try:
        return jsonify(get_pending_students(g.current_user['id_usuario'], _filters(),
                                            request.args.get('pagina', 1),
                                            request.args.get('busca', ''), pending_only=False)), 200
    except ValueError as error:
        return jsonify({'message': str(error)}), 400
        return jsonify({'message': 'Não foi possível consultar os alunos.'}), 500

@report_bp.route('/simulado/<simulado_id>', methods=['GET'])
@login_required(required_page='reports')
def simulado_detail(simulado_id):
    try:
        from Backend.services.report_service import get_simulado_detail
        return jsonify(get_simulado_detail(g.current_user['id_usuario'], simulado_id, _filters())), 200
    except ValueError as error:
        return jsonify({'message': str(error)}), 400
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'message': 'Não foi possível carregar os detalhes do simulado.'}), 500
