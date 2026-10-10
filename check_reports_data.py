import os
from dotenv import load_dotenv
load_dotenv('.env')
from Backend.services.report_service import get_reports_data

filters = {
    'ano': '2026',
    'bimestre': '3º BIMESTRE',
    'associacao': 'AAMAR'
}
data = get_reports_data(1, filters)
print("KPIs:", data['kpis'])
print("Escolas:", len(data['rankings'].get('escola', [])))
