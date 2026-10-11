import re

with open(r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_block = '''<div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 0.5rem;" id="paginasPermitidasCheckboxes">
                <label style="display:flex; align-items:center; gap:0.25rem;"><input type="checkbox" name="userPages" value="reports" checked> Visão Geral</label>
                <label style="display:flex; align-items:center; gap:0.25rem;"><input type="checkbox" name="userPages" value="paaeb" checked> PAAEB</label>
                <label style="display:flex; align-items:center; gap:0.25rem;"><input type="checkbox" name="userPages" value="data" checked> Dados</label>
             </div>'''

new_block = '''<div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 0.5rem;" id="paginasPermitidasCheckboxes">
                <label style="display:flex; align-items:center; gap:0.25rem; font-weight: 500;"><input type="checkbox" name="userPages" value="reports" checked> Visão Geral</label>
                <label style="display:flex; align-items:center; gap:0.25rem; font-weight: 500;"><input type="checkbox" name="userPages" value="paaeb" checked> PAAEB</label>
                <label style="display:flex; align-items:center; gap:0.25rem; font-weight: 500;"><input type="checkbox" name="userPages" value="enem" checked> ENEM</label>
                <label style="display:flex; align-items:center; gap:0.25rem; font-weight: 500;"><input type="checkbox" name="userPages" value="saeb" checked> SAEB</label>
                <label style="display:flex; align-items:center; gap:0.25rem; font-weight: 500;"><input type="checkbox" name="userPages" value="data" checked> Dados</label>
             </div>'''

if old_block in text:
    text = text.replace(old_block, new_block)
    with open(r'C:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Checkboxes updated.')
else:
    print('Block not found.')
