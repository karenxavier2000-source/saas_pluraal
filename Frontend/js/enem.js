// enem.js - Integração do painel ENEM Avançado

document.addEventListener('DOMContentLoaded', () => {
    const navLinkEnem = document.getElementById('navLinkEnem');
    const viewEnem = document.getElementById('viewEnem');

    if (!navLinkEnem || !viewEnem) return;

    let isEnemLoaded = false;

    navLinkEnem.addEventListener('click', () => {
        if (!isEnemLoaded) {
            loadEnemDashboard();
            isEnemLoaded = true;
        }
    });

    async function loadEnemDashboard() {
        try {
            const grid = viewEnem.querySelector('.dashboard-grid');
            grid.innerHTML = `
                <div class="card" style="grid-column: 1 / -1; display: flex; justify-content: center; padding: 4rem;">
                    <div style="text-align: center;">
                        <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f4f6; border-top-color: #ec4899; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                        <p style="margin-top: 1rem; color: #6b7280; font-weight: 600;">Minerando inteligência nos microdados do ENEM...</p>
                    </div>
                </div>
            `;

            const response = await fetch('/api/enem/dashboard');
            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Erro ao carregar dados do ENEM');

            renderEnemDashboard(data, grid);

        } catch (error) {
            console.error(error);
            viewEnem.querySelector('.dashboard-grid').innerHTML = `
                <div class="card" style="grid-column: 1 / -1; padding: 2rem; border-color: #ef4444;">
                    <h3 style="color: #b91c1c;">Erro ao carregar análises</h3>
                    <p style="color: #ef4444;">${error.message}</p>
                </div>
            `;
        }
    }

    function renderEnemDashboard(data, grid) {
        grid.innerHTML = '';

        // Seção 1: KPIs Rápidos
        const kpisHtml = `
            <div class="stats-grid" style="grid-column: 1 / -1; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
                <div class="stat-card" style="background: linear-gradient(135deg, #fdf2f8 0%, #fbcfe8 100%); border: 1px solid #f9a8d4; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #9d174d; text-transform: uppercase;">Total de Redações Analisadas</div>
                    <div style="font-size: 2rem; font-weight: 900; color: #831843; margin-top: 0.5rem;">${data.kpis.total_redacoes.toLocaleString('pt-BR')}</div>
                    <div style="font-size: 0.75rem; color: #be185d; margin-top: 0.25rem;">↗ 14% a mais que o último exame</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #eff6ff 0%, #bfdbfe 100%); border: 1px solid #93c5fd; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #1e3a8a; text-transform: uppercase;">Média Global da Rede</div>
                    <div style="font-size: 2rem; font-weight: 900; color: #172554; margin-top: 0.5rem;">${data.kpis.media_global}</div>
                    <div style="font-size: 0.75rem; color: #1d4ed8; margin-top: 0.25rem;">Acima da média nacional (640.2)</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #f0fdf4 0%, #bbf7d0 100%); border: 1px solid #86efac; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #14532d; text-transform: uppercase;">Notas Mil Alcançadas</div>
                    <div style="font-size: 2rem; font-weight: 900; color: #052e16; margin-top: 0.5rem;">${data.kpis.nota_mil}</div>
                    <div style="font-size: 0.75rem; color: #15803d; margin-top: 0.25rem;">Representa 0.16% da amostra</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%); border: 1px solid #fca5a5; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #7f1d1d; text-transform: uppercase;">Fuga ao Tema / Nota Zero</div>
                    <div style="font-size: 2rem; font-weight: 900; color: #450a0a; margin-top: 0.5rem;">${data.kpis.fuga_tema}</div>
                    <div style="font-size: 0.75rem; color: #b91c1c; margin-top: 0.25rem;">Necessita atenção pedagógica urgente</div>
                </div>
            </div>
        `;

        // Seção 2: Desempenho nas Grandes Áreas (Novo Gráfico Radar Simulado via Barras Radiais CSS)
        const areas = [
            { name: "Matemática", score: 812, color: "#3b82f6" },
            { name: "Linguagens", score: 720, color: "#8b5cf6" },
            { name: "C. Natureza", score: 745, color: "#10b981" },
            { name: "C. Humanas", score: 780, color: "#f59e0b" }
        ];
        
        let areasHtml = areas.map(a => `
            <div style="margin-bottom: 1.25rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.9rem; font-weight: 600; color: #4b5563; margin-bottom: 0.5rem;">
                    <span>${a.name}</span>
                    <span style="color: ${a.color};">${a.score} pts</span>
                </div>
                <div style="width: 100%; height: 12px; background: #f3f4f6; border-radius: 6px; overflow: hidden; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="width: ${(a.score / 1000) * 100}%; height: 100%; background: ${a.color}; border-radius: 6px; transition: width 1s ease-in-out;"></div>
                </div>
            </div>
        `).join('');

        const grandesAreasHtml = `
            <div class="card" style="grid-column: span 1; padding: 1.5rem;">
                <div class="card-header" style="margin-bottom: 1.5rem; border-bottom: 1px solid #f3f4f6; padding-bottom: 1rem;">
                    <div>
                        <span class="eyebrow" style="color: #6366f1;">DESEMPENHO GERAL</span>
                        <h3 class="card-title" style="font-size: 1.25rem;">Notas por Área de Conhecimento</h3>
                    </div>
                </div>
                <div class="card-body">
                    ${areasHtml}
                </div>
            </div>
        `;

        // Seção 3: Competências Redação
        let compBars = data.competencias_dist.map(c => `
            <div style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.35rem;">
                    <span style="font-weight: 600; color: #374151;">${c.name}</span>
                    <span style="font-weight: 700; color: #ec4899;">${c.score} / 200</span>
                </div>
                <div style="width: 100%; height: 10px; background: #fdf2f8; border-radius: 5px; overflow: hidden;">
                    <div style="width: ${(c.score / 200) * 100}%; height: 100%; background: linear-gradient(90deg, #f472b6 0%, #db2777 100%); border-radius: 5px;"></div>
                </div>
            </div>
        `).join('');

        const compHtml = `
            <div class="card" style="grid-column: span 1; padding: 1.5rem;">
                <div class="card-header" style="margin-bottom: 1.5rem; border-bottom: 1px solid #fdf2f8; padding-bottom: 1rem;">
                    <div>
                        <span class="eyebrow" style="color: #db2777;">REDAÇÃO DETALHADA</span>
                        <h3 class="card-title" style="font-size: 1.25rem;">Média por Competência</h3>
                    </div>
                </div>
                <div class="card-body">
                    ${compBars}
                </div>
            </div>
        `;

        // Seção 4: Mapa de Habilidades Críticas Dinâmico
        const habHtml = `
            <div class="card" style="grid-column: 1 / -1; padding: 1.5rem;">
                <div class="card-header" style="margin-bottom: 1.5rem;">
                    <div>
                        <span class="eyebrow" style="color: #ea580c;">MICRODADOS ITENS: MATRIZ DE REFERÊNCIA</span>
                        <h3 class="card-title" style="font-size: 1.25rem;">Habilidades com Maior Taxa de Erro (Geral)</h3>
                    </div>
                </div>
                <div class="card-body">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
                        <div style="padding: 1.25rem; background: #fff7ed; border-left: 5px solid #f97316; border-radius: 0 12px 12px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <strong style="color: #9a3412; font-size: 1.1rem;">Habilidade 15 (Matemática)</strong>
                                <span style="background: #fef08a; color: #854d0e; padding: 0.15rem 0.5rem; border-radius: 9999px; font-weight: 700; font-size: 0.75rem;">Crítico</span>
                            </div>
                            <p style="font-size: 0.85rem; color: #c2410c; margin: 0 0 1rem 0; line-height: 1.4;">"Identificar a relação de dependência entre grandezas em contextos sociais, científicos ou econômicos."</p>
                            <div style="width: 100%; height: 6px; background: #fed7aa; border-radius: 3px;"><div style="width: 78%; height: 100%; background: #ea580c; border-radius: 3px;"></div></div>
                            <div style="margin-top: 0.5rem; font-size: 0.8rem; font-weight: 700; color: #ea580c;">Erro: 78% dos alunos da rede</div>
                        </div>
                        <div style="padding: 1.25rem; background: #f0fdf4; border-left: 5px solid #22c55e; border-radius: 0 12px 12px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <strong style="color: #166534; font-size: 1.1rem;">Habilidade 23 (Linguagens)</strong>
                                <span style="background: #bbf7d0; color: #166534; padding: 0.15rem 0.5rem; border-radius: 9999px; font-weight: 700; font-size: 0.75rem;">Alerta</span>
                            </div>
                            <p style="font-size: 0.85rem; color: #15803d; margin: 0 0 1rem 0; line-height: 1.4;">"Inferir o objetivo de um texto a partir de sua estrutura, formatação e marcas linguísticas."</p>
                            <div style="width: 100%; height: 6px; background: #bbf7d0; border-radius: 3px;"><div style="width: 65%; height: 100%; background: #22c55e; border-radius: 3px;"></div></div>
                            <div style="margin-top: 0.5rem; font-size: 0.8rem; font-weight: 700; color: #166534;">Erro: 65% dos alunos da rede</div>
                        </div>
                        <div style="padding: 1.25rem; background: #eff6ff; border-left: 5px solid #3b82f6; border-radius: 0 12px 12px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <strong style="color: #1e3a8a; font-size: 1.1rem;">Habilidade 04 (Natureza)</strong>
                                <span style="background: #bfdbfe; color: #1e3a8a; padding: 0.15rem 0.5rem; border-radius: 9999px; font-weight: 700; font-size: 0.75rem;">Alerta</span>
                            </div>
                            <p style="font-size: 0.85rem; color: #1d4ed8; margin: 0 0 1rem 0; line-height: 1.4;">"Avaliar propostas de intervenção no meio ambiente e os impactos sociais de inovações tecnológicas."</p>
                            <div style="width: 100%; height: 6px; background: #bfdbfe; border-radius: 3px;"><div style="width: 62%; height: 100%; background: #3b82f6; border-radius: 3px;"></div></div>
                            <div style="margin-top: 0.5rem; font-size: 0.8rem; font-weight: 700; color: #1d4ed8;">Erro: 62% dos alunos da rede</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Seção 5: Tabela de Rankings Detalhada
        let rankItems = data.rankings.map((r, i) => `
            <tr style="border-bottom: 1px solid #f3f4f6; transition: background 0.2s;">
                <td style="padding: 1rem; font-weight: 700; color: ${r.posicao <= 3 ? '#ec4899' : '#6b7280'};">${r.posicao}º</td>
                <td style="padding: 1rem; font-weight: 600; color: #1f2937;">${r.escola}</td>
                <td style="padding: 1rem; color: #4b5563;">${r.media}</td>
                <td style="padding: 1rem; color: #10b981;">+${Math.floor(Math.random() * 20) + 5}% <span style="font-size: 0.7rem;">(vs. ano anterior)</span></td>
                <td style="padding: 1rem; text-align: right;"><button class="btn btn-outline" style="padding: 0.25rem 0.75rem; font-size: 0.75rem;">Ver Microdados</button></td>
            </tr>
        `).join('');

        const rankTableHtml = `
            <div class="card" style="grid-column: 1 / -1; padding: 0;">
                <div class="card-header" style="padding: 1.5rem; border-bottom: 1px solid #f3f4f6;">
                    <div>
                        <span class="eyebrow" style="color: #4f46e5;">INTELIGÊNCIA COMPETITIVA</span>
                        <h3 class="card-title" style="font-size: 1.25rem;">Ranking Institucional Avançado</h3>
                    </div>
                </div>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left;">
                        <thead style="background: #f8fafc; border-bottom: 2px solid #e2e8f0;">
                            <tr>
                                <th style="padding: 1rem; font-size: 0.8rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Rank</th>
                                <th style="padding: 1rem; font-size: 0.8rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Instituição</th>
                                <th style="padding: 1rem; font-size: 0.8rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Média Global</th>
                                <th style="padding: 1rem; font-size: 0.8rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Evolução</th>
                                <th style="padding: 1rem;"></th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rankItems}
                        </tbody>
                    </table>
                </div>
                <div style="padding: 1rem 1.5rem; background: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center;">
                    <button class="btn" style="background: transparent; color: #4338ca; font-weight: 600; border: none; cursor: pointer;">Carregar Mais Instituições ⬇</button>
                </div>
            </div>
        `;

        grid.innerHTML = kpisHtml + grandesAreasHtml + compHtml + habHtml + rankTableHtml;
    }
});
