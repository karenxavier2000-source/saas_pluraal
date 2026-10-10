import re

with open('Frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find where viewReports section ends.
# The next section starts with <!-- View 2: Data Dashboard --> or <section id="viewData"

idx = html.find('<!-- View 2: Data Dashboard -->')
if idx == -1:
    idx = html.find('<section id="viewProfile"')

if idx != -1:
    insertion = """
        <!-- Nova seção de Detalhamento de Simulados no final do dashboard -->
        <div class="card" style="margin-bottom: 2rem;">
          <div class="card-header">
            <h3>Simulados Disponíveis</h3>
            <p>Selecione um simulado para ver o resultado por aluno e por unidade.</p>
          </div>
          <div class="table-responsive">
            <table class="table" style="width: 100%; text-align: left; border-collapse: collapse;">
              <thead>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                  <th style="padding: 1rem; color: #64748b; font-size: 0.8rem;">ID SIMULADO</th>
                  <th style="padding: 1rem; color: #64748b; font-size: 0.8rem;">UNIÃO</th>
                  <th style="padding: 1rem; color: #64748b; font-size: 0.8rem;">ASSOCIAÇÃO</th>
                  <th style="padding: 1rem; color: #64748b; font-size: 0.8rem;">ESCOLA</th>
                  <th style="padding: 1rem; color: #64748b; font-size: 0.8rem;">AÇÕES</th>
                </tr>
              </thead>
              <tbody id="simuladosListTable">
                <!-- Preenchido via JS -->
                <tr style="border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background=''" onclick="openSimuladoModal('Exemplo')">
                  <td style="padding: 1rem; font-weight: 600; color: #3f4779;">SIM-2026-001</td>
                  <td style="padding: 1rem; color: #334155;">União Centro-Oeste Brasileira</td>
                  <td style="padding: 1rem; color: #334155;">Missão Tocantins</td>
                  <td style="padding: 1rem; color: #334155;">Colégio Adventista de Araguaina</td>
                  <td style="padding: 1rem;"><button class="btn" style="background: #e2e8f0; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer;">Ver Detalhes</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        """
    
    # inject just before the next view section
    html = html[:idx] + insertion + html[idx:]

# Also add the modal HTML just before </main>
modal_html = """
    <!-- Modal de Detalhamento de Simulado -->
    <div id="simuladoDetailModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 9999; align-items: center; justify-content: center; padding: 2rem;">
      <div style="background: #fff; width: 100%; max-width: 1200px; height: 90vh; border-radius: 12px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">
        
        <!-- Header -->
        <div style="padding: 1.5rem 2rem; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; background: #f8fafc;">
          <div>
            <h2 id="modalSimuladoTitle" style="color: #3f4779; margin: 0; font-size: 1.5rem; font-weight: 800;">Resultados do Simulado</h2>
            <p style="color: #64748b; margin: 0.25rem 0 0 0; font-size: 0.9rem;">Detalhamento de performance</p>
          </div>
          <button onclick="document.getElementById('simuladoDetailModal').style.display='none'" style="background: transparent; border: none; font-size: 1.5rem; color: #94a3b8; cursor: pointer;">&times;</button>
        </div>

        <!-- Tabs -->
        <div style="display: flex; gap: 1rem; padding: 0 2rem; border-bottom: 1px solid #e2e8f0; background: #f8fafc;">
          <button id="tabBtnAluno" onclick="switchSimuladoTab('aluno')" style="padding: 1rem 0; border: none; background: transparent; font-weight: 600; color: #528965; border-bottom: 3px solid #528965; cursor: pointer; font-size: 0.95rem;">Resultados por Aluno</button>
          <button id="tabBtnUnidade" onclick="switchSimuladoTab('unidade')" style="padding: 1rem 0; border: none; background: transparent; font-weight: 600; color: #64748b; border-bottom: 3px solid transparent; cursor: pointer; font-size: 0.95rem;">Resultados por Unidade</button>
        </div>

        <!-- Content -->
        <div style="flex: 1; overflow: auto; padding: 2rem; background: #f1f5f9;">
          
          <!-- Tab Aluno -->
          <div id="tabContentAluno" style="display: block;">
            <div style="background: #fff; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
              <div style="background: #528965; color: white; padding: 1rem 1.5rem; font-size: 0.85rem; font-weight: 600;">Resultados por Aluno</div>
              <div id="modalStudentsTable" style="display: flex; flex-direction: column;">
                <!-- Dummy Row -->
                <div style="padding: 1rem 1.5rem; display: grid; grid-template-columns: auto auto 1fr auto auto auto auto; gap: 1.5rem; align-items: center; border-bottom: 1px solid #f1f5f9;">
                  <input type="checkbox" style="width: 16px; height: 16px; border: 2px solid #cbd5e1; border-radius: 3px;">
                  <div style="width: 48px; height: 48px; border-radius: 50%; background: #f1f5f9; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #0f172a; font-size: 0.9rem;">50%</div>
                  <div>
                    <div style="font-weight: 700; color: #0f172a; font-size: 1rem; margin-bottom: 0.25rem;">Alberto Alves Godoy</div>
                    <div style="color: #94a3b8; font-size: 0.8rem;"><span style="display: inline-block; width: 4px; height: 4px; background: #cbd5e1; border-radius: 50%; margin: 0 4px 2px;"></span> EMERE03MA <span style="display: inline-block; width: 4px; height: 4px; background: #cbd5e1; border-radius: 50%; margin: 0 4px 2px;"></span> 30/30 Questões respondidas!</div>
                  </div>
                  <div style="color: #94a3b8; font-size: 0.85rem;">0h 0m</div>
                  <div style="text-align: center;">
                    <div style="font-weight: 700; color: #0f172a; font-size: 0.9rem; margin-bottom: 0.2rem;">49,97 %</div>
                    <span style="background: #74b868; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">Encerrada</span>
                  </div>
                  <div style="color: #94a3b8;">-</div>
                  <div style="font-weight: 500; color: #334155; font-size: 0.9rem;">50,00% (15/30)</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Tab Unidade -->
          <div id="tabContentUnidade" style="display: none;">
            <div style="background: #fff; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
              <div style="background: #528965; color: white; padding: 1rem 1.5rem; display: grid; grid-template-columns: 2fr 1fr 1.5fr 1fr 1fr 1fr 1fr 1.5fr; gap: 1rem; font-size: 0.8rem; font-weight: 600;">
                <div>União</div>
                <div>Campo</div>
                <div>Unidade</div>
                <div>Status</div>
                <div style="text-align: center;">Participantes</div>
                <div style="text-align: center;">Participantes esperados</div>
                <div style="text-align: center;">Percentual de participantes</div>
                <div style="text-align: right;">Desempenho Médio</div>
              </div>
              <div id="modalUnitsTable" style="display: flex; flex-direction: column;">
                <!-- Dummy Row -->
                <div style="padding: 1rem 1.5rem; display: grid; grid-template-columns: 2fr 1fr 1.5fr 1fr 1fr 1fr 1fr 1.5fr; gap: 1rem; align-items: center; font-size: 0.85rem; border-bottom: 1px solid #f1f5f9;">
                  <div style="color: #334155;">União Centro-Oeste Brasileira</div>
                  <div style="color: #334155;">Missão Tocantins</div>
                  <div style="color: #334155;">Colégio Adventista de Araguaina</div>
                  <div>
                    <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 0.2rem;">13/05/2026 - 05/06/2026</div>
                    <span style="background: #74b868; color: white; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">Encerrada</span>
                  </div>
                  <div style="text-align: center; color: #334155;">23</div>
                  <div style="text-align: center; color: #334155;">32</div>
                  <div style="text-align: center; color: #334155;">71,88%</div>
                  <div style="text-align: right; color: #334155; font-weight: 600;">57,25 %</div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
    
    <script>
      function openSimuladoModal(simuladoId) {
        document.getElementById('simuladoDetailModal').style.display = 'flex';
      }
      function switchSimuladoTab(tab) {
        if (tab === 'aluno') {
          document.getElementById('tabContentAluno').style.display = 'block';
          document.getElementById('tabContentUnidade').style.display = 'none';
          document.getElementById('tabBtnAluno').style.borderBottom = '3px solid #528965';
          document.getElementById('tabBtnAluno').style.color = '#528965';
          document.getElementById('tabBtnUnidade').style.borderBottom = '3px solid transparent';
          document.getElementById('tabBtnUnidade').style.color = '#64748b';
        } else {
          document.getElementById('tabContentAluno').style.display = 'none';
          document.getElementById('tabContentUnidade').style.display = 'block';
          document.getElementById('tabBtnUnidade').style.borderBottom = '3px solid #528965';
          document.getElementById('tabBtnUnidade').style.color = '#528965';
          document.getElementById('tabBtnAluno').style.borderBottom = '3px solid transparent';
          document.getElementById('tabBtnAluno').style.color = '#64748b';
        }
      }
    </script>
"""

main_end = html.rfind('</main>')
if main_end != -1:
    html = html[:main_end] + modal_html + html[main_end:]

with open('Frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
