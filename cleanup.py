import re

with open('Frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the injected button
btn_pattern = r'<button[^>]*>Ver Tela de Simulado Teste</button>'
html = re.sub(btn_pattern, '', html)

# Remove the injected view
if '<!-- ================= SIMULADO DETAIL VIEW ================= -->' in html:
    html = html.split('<!-- ================= SIMULADO DETAIL VIEW ================= -->')[0]
    html += '\n    </main>\n  </div>\n</body>\n</html>'

with open('Frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
