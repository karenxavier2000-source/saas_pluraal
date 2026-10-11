import re

with open('Frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

btn = """<button onclick="document.querySelectorAll('.view-content').forEach(el => el.classList.add('hidden')); document.getElementById('viewSimuladoDetail').classList.remove('hidden');" class="btn btn-primary" style="background: #528965; color: white; border-radius: 8px; padding: 0.5rem 1rem; margin-top: 1rem;">Ver Tela de Simulado Teste</button>"""

if "Ver Tela de Simulado Teste" not in html:
    html = html.replace('<div class="report-hero">', '<div class="report-hero">' + btn)

with open('Frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
