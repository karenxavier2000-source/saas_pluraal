import re
path = r'c:\Users\karen.xavier\Desktop\pluraal saas\Frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_tabs = '''          <div class="rank-tabs" role="tablist" id="dataTabs" style="margin-bottom: 2rem;">
            <button class="active" data-data-tab="simulados">Dados Simulados</button>
            <button data-data-tab="paaeb">Dados PAAEB</button>
          </div>'''
new_tabs = '''          <div class="rank-tabs" role="tablist" id="dataTabs" style="margin-bottom: 2rem;">
            <button class="active" data-data-tab="simulados">Dados Simulados</button>
            <button data-data-tab="paaeb">Dados PAAEB</button>
            <button data-data-tab="escolas" id="btnTabEscolas" style="display:none;">Cadastrar Escolas</button>
          </div>'''

content = content.replace(old_tabs, new_tabs)

old_end = '''            <p class="data-scope-note" style="margin-top:1rem; font-size:0.85rem; color:var(--text-muted);">
              Esta exportação traz as mesmas tabelas de gabaritos e alunos, mas aplicadas ao universo de simulados PAAEB.
            </p>
          </div>
      </section>'''
new_end = '''            <p class="data-scope-note" style="margin-top:1rem; font-size:0.85rem; color:var(--text-muted);">
              Esta exportação traz as mesmas tabelas de gabaritos e alunos, mas aplicadas ao universo de simulados PAAEB.
            </p>
          </div>
          
          <!-- BANCO DE ESCOLAS -->
          <div id="dataEscolasContent" class="data-export-grid hidden">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; grid-column: 1 / -1;">
              <h3 style="font-size: 1.25rem; font-weight: 600;">Banco de Escolas</h3>
              <button class="btn btn-primary" id="btnNewSchool">+ Nova Escola</button>
            </div>
            
            <div class="card" style="padding: 0; grid-column: 1 / -1;">
              <div class="table-responsive">
                <table class="data-table" style="min-width: 800px;">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>União</th>
                      <th>Sigla União</th>
                      <th>Associação</th>
                      <th>Sigla Ass.</th>
                      <th>Escola</th>
                      <th style="width: 150px; text-align: center;">Ações</th>
                    </tr>
                  </thead>
                  <tbody id="schoolTableBody">
                    <!-- Loaded via JS -->
                  </tbody>
                </table>
              </div>
            </div>
          </div>
      </section>'''

content = content.replace(old_end, new_end)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated index.html')
