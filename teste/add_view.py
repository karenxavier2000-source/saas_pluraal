import re

with open('Frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

new_view = """
      <!-- ================= SIMULADO DETAIL VIEW ================= -->
      <div id="viewSimuladoDetail" class="content-view hidden">
        <div class="report-header" style="margin-bottom: 2rem;">
          <div>
            <button onclick="document.getElementById('viewSimuladoDetail').classList.add('hidden'); document.getElementById('viewReports').classList.remove('hidden');" class="btn btn-outline" style="margin-bottom: 1rem; border: none; background: transparent; padding: 0; display: flex; align-items: center; gap: 0.5rem; color: #64748b; cursor: pointer;">
              <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
              Voltar aos relatórios
            </button>
            <h1 id="simuladoDetailTitle" style="color: #3f4779; font-size: 1.5rem; font-weight: 800; margin-bottom: 0.25rem;">Resultados do Simulado</h1>
            <p style="color: #64748b; font-size: 0.9rem;">Detalhamento por alunos e por unidade</p>
          </div>
        </div>

        <div class="card" style="margin-bottom: 2rem; border-radius: 12px; border: 1px solid #e2e8f0; background: #fff; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
          <div style="background: #528965; color: white; padding: 1rem 1.5rem; display: grid; grid-template-columns: 2fr 1fr 1.5fr 1fr 1fr 1fr 1fr 1.5fr; gap: 1rem; font-size: 0.8rem; font-weight: 600;">
            <div>União</div>
            <div>Campo</div>
            <div>Unidade</div>
            <div>Status</div>
            <div style="text-align: center;">Participantes</div>
            <div style="text-align: center;">Participantes esperados</div>
            <div style="text-align: center;">Percentual de participantes</div>
            <div style="text-align: right;">Ciências Humanas e suas Tecnologias</div>
          </div>
          <div id="simuladoUnitsTable" style="display: flex; flex-direction: column;">
            <!-- Dummy row -->
            <div style="padding: 1rem 1.5rem; display: grid; grid-template-columns: 2fr 1fr 1.5fr 1fr 1fr 1fr 1fr 1.5fr; gap: 1rem; align-items: center; font-size: 0.85rem; border-bottom: 1px solid #f1f5f9;">
              <div style="color: #334155;">União Centro-Oeste Brasileira</div>
              <div style="color: #334155;">Missão Tocantins</div>
              <div style="color: #334155;">Colégio Adventista de Araguaina</div>
              <div>
                <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 0.2rem;">13/05/2026 00:00 até 05/06/2026 23:59</div>
                <span style="background: #74b868; color: white; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">Encerrada</span>
              </div>
              <div style="text-align: center; color: #334155;">23</div>
              <div style="text-align: center; color: #334155;">32</div>
              <div style="text-align: center; color: #334155;">71,88%</div>
              <div style="text-align: right; color: #334155;">57,25 %</div>
            </div>
          </div>
        </div>

        <div class="card" style="border-radius: 12px; border: 1px solid #e2e8f0; background: #fff; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
          <div style="background: #528965; color: white; padding: 1rem 1.5rem; font-size: 0.8rem; font-weight: 600;">
            Resultados por Aluno
          </div>
          <div id="simuladoStudentsTable" style="display: flex; flex-direction: column;">
            <!-- Dummy student row -->
            <div style="padding: 1rem 1.5rem; display: grid; grid-template-columns: auto auto 1fr auto auto auto auto; gap: 1.5rem; align-items: center; border-bottom: 1px solid #f1f5f9;">
              <input type="checkbox" style="width: 16px; height: 16px; border: 2px solid #cbd5e1; border-radius: 3px;">
              <div style="width: 48px; height: 48px; border-radius: 50%; background: #f1f5f9; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #0f172a; font-size: 0.9rem;">
                50%
              </div>
              <div>
                <div style="font-weight: 700; color: #0f172a; font-size: 1rem; margin-bottom: 0.25rem;">Alberto Alves Godoy</div>
                <div style="color: #94a3b8; font-size: 0.8rem;">
                  <span style="display: inline-block; width: 4px; height: 4px; background: #cbd5e1; border-radius: 50%; margin: 0 4px 2px;"></span> EMERE03MA 
                  <span style="display: inline-block; width: 4px; height: 4px; background: #cbd5e1; border-radius: 50%; margin: 0 4px 2px;"></span> 30/30 Questões respondidas!
                </div>
              </div>
              <div style="color: #94a3b8; font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem;">
                0h 0m
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              </div>
              <div style="text-align: center;">
                <div style="font-weight: 700; color: #0f172a; font-size: 0.9rem; margin-bottom: 0.2rem;">49,97 %</div>
                <span style="background: #74b868; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">Encerrada</span>
              </div>
              <div style="color: #94a3b8;">-</div>
              <div style="font-weight: 500; color: #334155; font-size: 0.9rem;">
                50,00% (15/30)
              </div>
            </div>
          </div>
        </div>
      </div>
"""

html = html.replace('</main>', new_view + '\n    </main>')

with open('Frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
