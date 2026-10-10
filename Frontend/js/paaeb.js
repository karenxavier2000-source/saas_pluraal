document.addEventListener('DOMContentLoaded', () => {
    const navLinkPaaeb = document.getElementById('navLinkPaaeb');
    const viewPaaeb = document.getElementById('viewPaaeb');

    if (!navLinkPaaeb || !viewPaaeb) return;

    let isPaaebLoaded = false;
    let requestSequence = 0;
    let historyObserver = null;

    const loadIfActive = () => {
        if (window.location.hash.replace('#', '') === 'paaeb' && !isPaaebLoaded) {
            const urlParams = new URLSearchParams(window.location.search);
            const initialFilters = {};
            for (const [key, value] of urlParams.entries()) {
                if (['uniao', 'associacao', 'escola', 'serie'].includes(key)) {
                    initialFilters[key] = value;
                }
            }
            loadPaaebDashboard(initialFilters);
            isPaaebLoaded = true;
        }
    };

    navLinkPaaeb.addEventListener('click', () => {
        if (!isPaaebLoaded) {
            loadPaaebDashboard();
            isPaaebLoaded = true;
        }
    });

    window.addEventListener('hashchange', loadIfActive);
    loadIfActive();

    async function loadPaaebDashboard(filters = {}) {
        const sequence = ++requestSequence;
        const grid = viewPaaeb.querySelector('.paaeb-grid');
        grid.innerHTML = `
            <div class="paaeb-loading" role="status" aria-live="polite">
                <div class="paaeb-loading__spinner" aria-hidden="true"></div>
                <p>Carregando os indicadores do PAAEB…</p>
            </div>
        `;

        try {
            const params = new URLSearchParams(filters);
            const data = await API.request(`/api/paaeb/dashboard?${params}`);
            if (sequence !== requestSequence) return;
            renderPaaebDashboard(grid, data, filters);
        } catch (error) {
            if (sequence === requestSequence) {
                isPaaebLoaded = false;
                grid.innerHTML = `<div class="paaeb-error" role="alert"></div>`;
                grid.firstElementChild.textContent = error.message || 'Não foi possível carregar os dados do PAAEB.';
            }
        }
    }

    function renderPaaebDashboard(grid, data, filters) {
        historyObserver?.disconnect();
        grid.innerHTML = '';
        const latestYear = [...new Set(data.history.map(row => row.ano))].sort().at(-1);
        const latest = data.history.filter(row => row.ano === latestYear);
        const media = (part) => latest.find(row => row.materia?.toLowerCase().includes(part))?.media;
        const format = (value) => value == null ? '—' : Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 1 });
        const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char =>
            ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
        const displaySerie = (data.serie || '—').replace(/ ano$/i, ' Ano');
        const mediaValue = part => media(part) || 0;
        
        // Find the level where the average proficiency falls into the 'pontos_na_escala' range
        const mappedLevel = part => {
            const avg = mediaValue(part);
            const levels = (data.levels || []).filter(row => row.ano === latestYear && row.materia?.toLowerCase().includes(part));
            
            for (const level of levels) {
                if (!level.pontos_na_escala) continue;
                // Parse "225 - 250" or "0 - 150" or "350 - 375"
                const parts = level.pontos_na_escala.split('-').map(s => parseFloat(s.trim().replace(',', '.')));
                if (parts.length === 2) {
                    const [min, max] = parts;
                    if (avg >= min && avg <= max) {
                        return level;
                    }
                }
            }
            // fallback if not found in ranges, maybe highest level if it exceeds?
            if (levels.length > 0) {
                // Return highest if avg is higher than all maxes, or lowest if lower than all mins
                const sorted = [...levels].sort((a, b) => {
                    const minA = parseFloat(a.pontos_na_escala?.split('-')[0] || 0);
                    const minB = parseFloat(b.pontos_na_escala?.split('-')[0] || 0);
                    return minA - minB;
                });
                if (avg > parseFloat(sorted[sorted.length - 1].pontos_na_escala?.split('-')[1] || 0)) return sorted[sorted.length - 1];
                return sorted[0];
            }
            return null;
        };

        const levelNumber = part => mappedLevel(part)?.nivel_adq?.match(/\d+/)?.[0] || '—';
        const adequacyName = part => escapeHtml(mappedLevel(part)?.adequacao || '—');
        
        const years = [...new Set(data.history.map(row => row.ano))].sort();
        const valuesFor = (part) => years.map(year =>
            data.history.find(row => row.ano === year && row.materia?.toLowerCase().includes(part))?.media ?? null);

        // SEÇÃO 0: Hero com fundo azul marinho gradiente igual à imagem
        const heroHtml = `
            <div style="background: linear-gradient(90deg, #42416b 0%, #68809a 100%); border-radius: 12px; padding: 2.5rem; position: relative; overflow: hidden; margin-bottom: 2rem; border-bottom: 5px solid transparent; border-image: linear-gradient(90deg, #facc15 0%, #10b981 33%, #ef4444 66%, #3b82f6 100%) 1; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="position: relative; z-index: 2; display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
                    <div>
                        <span style="color: #cbd5e1; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; display: flex; align-items: center; gap: 0.5rem;">
                            <div style="width: 20px; height: 1px; background: #cbd5e1;"></div>
                            AVALIAÇÃO EXTERNA
                        </span>
                        <h1 style="color: #ffffff; font-size: 2.5rem; font-weight: 800; margin: 0.5rem 0;">Análise PAAEB</h1>
                        <p style="color: #e2e8f0; font-size: 1rem; margin: 0;">Síntese dos Indicadores de Aprendizagem, Proficiência e Adequação.</p>
                    </div>
                    <div class="paaeb-hero-actions" style="display: flex; gap: 0.75rem; align-items: center; z-index: 10;">
                        <button id="paaebShareBtn" style="display: flex; align-items: center; gap: 0.5rem; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); color: #fff; padding: 0.6rem 1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: all 0.2s;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
                            Compartilhar Link
                        </button>
                        <button id="paaebExportPdfBtn" style="display: flex; align-items: center; gap: 0.5rem; background: #fff; border: none; color: #1e293b; padding: 0.6rem 1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                            Exportar PDF
                        </button>
                    </div>
                </div>
            </div>
        `;

        const periodsHtml = (data.periods || []).map(item => `
            <div class="paaeb-period">
                <strong>${escapeHtml(item.label)}</strong>
                <span>${item.years.length ? item.years.map(escapeHtml).join(', ') : 'Sem dados nesta seleção'}</span>
            </div>
        `).join('');

        // Filtros solicitados
        const filterHtml = `
            <div class="paaeb-filters" style="display: flex; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap; background: #fff; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; align-items: center;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #475569;">Filtros:</div>
                <select id="paaebUniao" aria-label="União" style="padding: 0.5rem 1rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.85rem; color: #334155; min-width: 180px; flex: 1;">
                    <option value="">Todas as Uniões</option>
                </select>
                <select id="paaebAssociacao" aria-label="Associação" style="padding: 0.5rem 1rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.85rem; color: #334155; min-width: 180px; flex: 1;">
                    <option value="">Todas as Associações</option>
                </select>
                <select id="paaebEscola" aria-label="Escola" style="padding: 0.5rem 1rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.85rem; color: #334155; min-width: 250px; flex: 2;">
                    <option value="">Todas as Escolas</option>
                </select>
                <select id="paaebSerie" aria-label="Série" style="padding: 0.5rem 1rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.85rem; color: #334155; min-width: 160px; flex: 1;">
                </select>
                <div class="paaeb-periods" aria-label="Disponibilidade dos dados">
                    <div class="paaeb-periods-heading">Anos disponíveis nesta seleção · ${escapeHtml(data.serie || '—')} · síntese: ${escapeHtml(latestYear || '—')}</div>
                    <div class="paaeb-periods-grid">${periodsHtml}</div>
                </div>
            </div>
        `;

        // SEÇÃO 1: Síntese dos Indicadores (Estilo bem clean igual ao print)
        const sinteseHtml = `
            <div class="paaeb-summary" style="margin-bottom: 3rem;">
                <h3 style="font-size: 1.15rem; color: #1e293b; font-weight: 700; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">Síntese dos Indicadores de Aprendizagem</h3>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem 1rem; width: 150px; text-align: center; background: #fff; position: relative;">
                        <span style="position: absolute; top: 8px; right: 8px; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                        <div style="font-size: 2rem; color: #3b82f6; font-weight: 700; margin-bottom: 0.25rem;">${escapeHtml(displaySerie)}</div>
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Série</div>
                    </div>
                    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem 1rem; width: 150px; text-align: center; background: #fff; position: relative;">
                        <span style="position: absolute; top: 8px; right: 8px; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                        <div style="font-size: 2rem; color: #1e293b; font-weight: 700; margin-bottom: 0.25rem;">${format(data.students)}</div>
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Alunos avaliados</div>
                    </div>
                </div>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1rem;">
                    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem 1rem; width: 150px; text-align: center; background: #fff; position: relative;">
                        <span style="position: absolute; top: 8px; right: 8px; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                        <div style="font-size: 2rem; color: #1e293b; font-weight: 700; margin-bottom: 0.25rem;">${format(media('portugues'))}</div>
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Proficiência LG</div>
                    </div>
                    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem 1rem; width: 150px; text-align: center; background: #fff; position: relative;">
                        <span style="position: absolute; top: 8px; right: 8px; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                        <div style="font-size: 2rem; color: #1e293b; font-weight: 700; margin-bottom: 0.25rem;">${levelNumber('portugues')}</div>
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Nível LG</div>
                    </div>
                    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem 1rem; width: 220px; text-align: center; background: #fff; position: relative;">
                        <span style="position: absolute; top: 8px; right: 8px; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                        <div style="font-size: 2rem; color: #475569; font-weight: 700; margin-bottom: 0.25rem;">${adequacyName('portugues')}</div>
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Adequação LG</div>
                    </div>
                </div>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1rem;">
                    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem 1rem; width: 150px; text-align: center; background: #fff; position: relative;">
                        <span style="position: absolute; top: 8px; right: 8px; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                        <div style="font-size: 2rem; color: #1e293b; font-weight: 700; margin-bottom: 0.25rem;">${format(media('matem'))}</div>
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Proficiência MT</div>
                    </div>
                    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem 1rem; width: 150px; text-align: center; background: #fff; position: relative;">
                        <span style="position: absolute; top: 8px; right: 8px; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                        <div style="font-size: 2rem; color: #1e293b; font-weight: 700; margin-bottom: 0.25rem;">${levelNumber('matem')}</div>
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Nível MT</div>
                    </div>
                    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem 1rem; width: 220px; text-align: center; background: #fff; position: relative;">
                        <span style="position: absolute; top: 8px; right: 8px; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                        <div style="font-size: 2rem; color: #475569; font-weight: 700; margin-bottom: 0.25rem;">${adequacyName('matem')}</div>
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Adequação MT</div>
                    </div>
                </div>
            </div>
        `;

        // SEÇÃO 2: Histórico de proficiência
        const mtData = valuesFor('matem');
        const lgData = valuesFor('portugues');
        const latestValue = values => {
            for (let index = values.length - 1; index >= 0; index--) {
                if (Number.isFinite(values[index])) return { value: values[index], year: years[index] };
            }
            return null;
        };
        const mtLatest = latestValue(mtData);
        const lgLatest = latestValue(lgData);

        const historyChartHtml = `
            <div class="paaeb-history-card">
                <div class="paaeb-history-legend">
                    <div class="paaeb-history-series paaeb-history-math">
                        <span class="paaeb-history-dot" aria-hidden="true"></span>
                        <span>Matemática</span>
                        <strong>${format(mtLatest?.value)}</strong>
                        <small>${escapeHtml(mtLatest?.year || '')}</small>
                    </div>
                    <div class="paaeb-history-series paaeb-history-language">
                        <span class="paaeb-history-dot" aria-hidden="true"></span>
                        <span>Língua Portuguesa</span>
                        <strong>${format(lgLatest?.value)}</strong>
                        <small>${escapeHtml(lgLatest?.year || '')}</small>
                    </div>
                </div>
                <div class="paaeb-history-plot">
                    <svg class="paaeb-history-svg" role="img" aria-label="Histórico de proficiência em Matemática e Língua Portuguesa"></svg>
                </div>
            </div>
        `;

        const drawHistoryChart = () => {
            const plot = grid.querySelector('.paaeb-history-plot');
            const svg = plot?.querySelector('svg');
            if (!svg) return;
            const width = Math.max(280, Math.round(plot.clientWidth));
            const height = 240;
            const left = 46, right = 18, top = 22, bottom = 38;
            const chartWidth = width - left - right;
            const chartHeight = height - top - bottom;
            const allValues = [...mtData, ...lgData].filter(Number.isFinite);
            if (!allValues.length) {
                svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
                svg.innerHTML = `<text x="${width / 2}" y="${height / 2}" text-anchor="middle" fill="#64748b" font-size="14">Sem dados nesta seleção</text>`;
                return;
            }
            const minimum = Math.floor((Math.min(...allValues) - 15) / 20) * 20;
            const maximum = Math.max(minimum + 40, Math.ceil((Math.max(...allValues) + 15) / 20) * 20);
            const valueRange = maximum - minimum;
            const x = index => left + (years.length === 1 ? chartWidth / 2 : index * chartWidth / (years.length - 1));
            const y = value => top + (maximum - value) / valueRange * chartHeight;
            const gridLines = Array.from({ length: 5 }, (_, index) => {
                const value = minimum + index * valueRange / 4;
                const lineY = y(value);
                return `<line x1="${left}" y1="${lineY}" x2="${width - right}" y2="${lineY}" stroke="#e9edf5" stroke-width="1" />
                    <text x="${left - 10}" y="${lineY + 4}" text-anchor="end" fill="#8794aa" font-size="11">${Math.round(value)}</text>`;
            }).join('');
            const maxLabels = Math.max(2, Math.floor(chartWidth / 62));
            const labelStep = Math.max(1, Math.ceil((years.length - 1) / (maxLabels - 1)));
            const yearLabels = years.map((year, index) =>
                (index === 0 || index === years.length - 1 || index % labelStep === 0)
                    ? `<text x="${x(index)}" y="${height - 16}" text-anchor="middle" fill="#8794aa" font-size="11">${escapeHtml(year)}</text>`
                    : '').join('');
            const seriesMarkup = (values, color, label, offsetY) => {
                const points = values.map((value, index) => Number.isFinite(value) ? { value, index } : null);
                const line = points.map((point, index) => point ? `${index === 0 || !points[index - 1] ? 'M' : 'L'} ${x(index)} ${y(point.value)}` : '').join(' ');
                const dots = points.filter(Boolean).map(point => `
                    <circle cx="${x(point.index)}" cy="${y(point.value)}" r="4" fill="#fff" stroke="${color}" stroke-width="2.5" tabindex="0" aria-label="${label}, ${escapeHtml(years[point.index])}: ${format(point.value)}">
                        <title>${label} · ${escapeHtml(years[point.index])}: ${format(point.value)}</title>
                    </circle>
                    <text x="${x(point.index)}" y="${y(point.value) + offsetY}" text-anchor="middle" fill="${color}" font-size="10" font-weight="700" paint-order="stroke" stroke="#fff" stroke-width="3">${format(point.value)}</text>
                `).join('');
                return `<path d="${line}" fill="none" stroke="${color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />${dots}`;
            };
            svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
            svg.innerHTML = gridLines + yearLabels
                + seriesMarkup(mtData, '#c67610', 'Matemática', -12)
                + seriesMarkup(lgData, '#5554e8', 'Língua Portuguesa', 20)
                + `<text x="${width / 2}" y="${height - 2}" text-anchor="middle" fill="#8794aa" font-size="11">ano</text>`;
        };

        const proficienciaHtml = `
            <div style="margin-bottom: 3rem;">
                <h3 style="font-size: 1.15rem; color: #1e293b; font-weight: 700; margin-bottom: 0.5rem;">Proficiência Média</h3>
                <div style="border-bottom: 1px solid #cbd5e1; margin-bottom: 1rem;"></div>
                <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; background: #fff; margin-bottom: 2rem;">
                    <p style="color: #475569; font-size: 0.9rem; line-height: 1.6; margin-bottom: 1rem;">O PAAEB utiliza a Teoria da Resposta ao Item (TRI) para estimar a proficiência dos alunos, permitindo a comparação de resultados entre anos e provas diferentes.</p>
                    <p style="color: #475569; font-size: 0.9rem; line-height: 1.6;">O gráfico a seguir apresenta a evolução das proficiências médias em Matemática (MT) e Língua Portuguesa (LG), evidenciando o desempenho da instituição ao longo do tempo.</p>
                </div>
                <h3 style="font-size: 1.15rem; color: #1e293b; font-weight: 700; margin-bottom: 1rem;">Histórico proficiência</h3>
                ${historyChartHtml}
            </div>
        `;

        // SEÇÃO 3: Distribuição Scatter Plot
        const scatterColors = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444'];
        const allScatterYears = [...new Set((data.scatter || []).map(s => s.ano))].sort().reverse();
        const scatterYearOptions = allScatterYears.map(y => `<option value="${escapeHtml(y)}" ${y === latestYear ? 'selected' : ''}>Ano: ${escapeHtml(y)}</option>`).join('');

        const distHtml = `
            <div style="margin-bottom: 3rem;">
                <h3 style="font-size: 1.15rem; color: #1e293b; font-weight: 700; margin-bottom: 1rem;">Distribuição percentual dos alunos da Escola na escala de proficiência</h3>
                <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; background: #fff; margin-bottom: 1rem;">
                    <p style="color: #475569; font-size: 0.9rem; line-height: 1.6; margin-bottom: 1rem;">O gráfico a seguir apresenta a dispersão das proficiências médias em Língua Portuguesa (eixo Y) e Matemática (eixo X), considerando os resultados dos alunos avaliados no PAAEB.</p>
                    <p style="color: #475569; font-size: 0.9rem; line-height: 1.6; margin-bottom: 1rem;">Cada ponto representa o desempenho combinado de uma turma, escola ou grupo de estudantes, permitindo observar tendências de correlação entre as duas áreas.</p>
                    <p style="color: #475569; font-size: 0.9rem; line-height: 1.6; margin-bottom: 1rem;">Em geral, nota-se que alunos com maior desempenho em Matemática também tendem a apresentar melhores resultados em Língua Portuguesa, evidenciando a interdependência das competências cognitivas e linguísticas que sustentam o aprendizado nas diferentes disciplinas.</p>
                    <p style="color: #475569; font-size: 0.9rem; line-height: 1.6;">Esse tipo de análise contribui para uma visão integrada do desempenho, apoiando decisões pedagógicas que considerem o desenvolvimento global do estudante.</p>
                </div>
                
                <div class="paaeb-scatter-layout" style="display: flex; gap: 1rem; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; padding: 1.5rem; min-height: 400px; position: relative;">
                    <div style="position: absolute; top: 1rem; right: 1rem; z-index: 10;">
                        <select id="scatterYearSelect" style="border: 1px solid #e2e8f0; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; color: #64748b; background: #f8fafc; cursor: pointer; outline: none;">
                            ${scatterYearOptions || `<option value="">Sem dados</option>`}
                        </select>
                    </div>
                    <span style="position: absolute; top: 1.25rem; right: 8rem; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                    
                    <div class="paaeb-scatter-legend" style="width: 250px; padding-right: 1rem; overflow-y: auto; max-height: 400px;">
                        <ul id="scatterLegend" style="list-style: none; padding: 0; margin: 0; font-size: 0.8rem; color: #475569;">
                        </ul>
                    </div>
                    <div style="flex: 1; position: relative; margin-left: 3rem;" id="scatterPlotContainer">
                        <!-- Scatter content goes here -->
                    </div>
                </div>
                <div id="scatterAnalysisContainer" style="margin-top: 1rem;"></div>
            </div>
        `;

        const drawScatterChart = (selectedYear) => {
            const plotContainer = grid.querySelector('#scatterPlotContainer');
            const legend = grid.querySelector('#scatterLegend');
            if (!plotContainer || !legend) return;

            const yearData = (data.scatter || []).filter(s => s.ano === selectedYear);
            const scatterScores = yearData.flatMap(group => [group.matematica, group.portugues]);
            const scatterMin = scatterScores.length ? Math.floor(Math.min(...scatterScores) / 30) * 30 : 210;
            const scatterMax = scatterScores.length ? Math.max(scatterMin + 120, Math.ceil(Math.max(...scatterScores) / 30) * 30) : 330;
            const scatterRange = scatterMax - scatterMin;

            const scatterDots = yearData.map((student, index) => {
                const cx = Math.max(5, Math.min(95, (student.matematica - scatterMin) / scatterRange * 90 + 5));
                const cy = Math.max(5, Math.min(95, 95 - (student.portugues - scatterMin) / scatterRange * 90));
                return `<circle cx="${cx}%" cy="${cy}%" r="6" fill="${scatterColors[index % scatterColors.length]}" opacity="0.8"><title>${escapeHtml(student.nome)} (MT: ${student.matematica}, LG: ${student.portugues})</title></circle>`;
            }).join('');

            plotContainer.innerHTML = `
                <!-- Eixos com grid lines iguais ao print -->
                <div style="position: absolute; left: 0; bottom: 0; width: 100%; height: 1px; border-top: 1px dashed #cbd5e1;"></div>
                <div style="position: absolute; left: 0; bottom: 25%; width: 100%; height: 1px; border-top: 1px dashed #cbd5e1;"></div>
                <div style="position: absolute; left: 0; bottom: 50%; width: 100%; height: 1px; border-top: 1px dashed #cbd5e1;"></div>
                <div style="position: absolute; left: 0; bottom: 75%; width: 100%; height: 1px; border-top: 1px dashed #cbd5e1;"></div>
                <div style="position: absolute; left: 0; bottom: 100%; width: 100%; height: 1px; border-top: 1px dashed #cbd5e1;"></div>
                
                <div style="position: absolute; left: 0; top: 0; width: 1px; height: 100%; background: #cbd5e1;"></div>
                <div style="position: absolute; left: 0; top: 60%; width: 100%; height: 1px; border-top: 2px dashed #64748b;"></div>
                
                <svg width="100%" height="100%" style="overflow: visible;">
                    ${scatterDots || '<text x="50%" y="50%" text-anchor="middle" fill="#64748b" font-size="12">Sem dados para este ano</text>'}
                </svg>
                
                <!-- Rótulos Y -->
                <div style="position: absolute; left: -30px; bottom: 0px; font-size: 0.75rem; color: #64748b;">${Math.round(scatterMin)}</div>
                <div style="position: absolute; left: -30px; bottom: 25%; font-size: 0.75rem; color: #64748b;">${Math.round(scatterMin + scatterRange * .25)}</div>
                <div style="position: absolute; left: -30px; bottom: 50%; font-size: 0.75rem; color: #64748b;">${Math.round(scatterMin + scatterRange * .5)}</div>
                <div style="position: absolute; left: -30px; bottom: 75%; font-size: 0.75rem; color: #64748b;">${Math.round(scatterMin + scatterRange * .75)}</div>
                <div style="position: absolute; left: -30px; top: -5px; font-size: 0.75rem; color: #64748b;">${Math.round(scatterMax)}</div>
                <div style="position: absolute; left: -65px; top: 50%; transform: translateY(-50%) rotate(180deg); writing-mode: vertical-rl; font-size: 0.8rem; color: #64748b; font-weight: 700; white-space: nowrap;">Língua Portuguesa</div>
            `;

            legend.innerHTML = yearData.map((student, index) => `
                <li style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="display:flex; align-items:center;">
                        <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${scatterColors[index % scatterColors.length]}; margin-right:8px; flex-shrink: 0;"></span>
                        <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px;" title="${escapeHtml(student.nome)}">${escapeHtml(student.nome)}</span>
                    </span>
                </li>
            `).join('');

            const analysisContainer = grid.querySelector('#scatterAnalysisContainer');
            if (analysisContainer) {
                if (yearData.length > 0) {
                    const mtScores = yearData.map(s => s.matematica);
                    const lgScores = yearData.map(s => s.portugues);
                    const avgMt = mtScores.reduce((a, b) => a + b, 0) / mtScores.length;
                    const avgLg = lgScores.reduce((a, b) => a + b, 0) / lgScores.length;
                    
                    const q1 = yearData.filter(s => s.matematica > avgMt && s.portugues > avgLg).length;
                    const q3 = yearData.filter(s => s.matematica <= avgMt && s.portugues <= avgLg).length;
                    
                    const total = yearData.length;
                    const percentQ1 = ((q1 / total) * 100).toFixed(1);
                    const percentQ3 = ((q3 / total) * 100).toFixed(1);
                    
                    let trendText = "";
                    if (avgMt > avgLg + 10) {
                        trendText = "O grupo avaliado apresenta, em média, maior facilidade com o raciocínio lógico-matemático do que com as competências de leitura e interpretação linguística.";
                    } else if (avgLg > avgMt + 10) {
                        trendText = "O grupo avaliado apresenta, no geral, maior consolidação das habilidades de leitura e linguagem do que do pensamento lógico-matemático.";
                    } else {
                        trendText = "Observa-se um desenvolvimento equilibrado e estatisticamente alinhado entre as duas grandes áreas do conhecimento avaliadas.";
                    }

                    const correlationText = (q1 + q3) / total > 0.65 
                        ? "Existe uma forte correlação positiva visível na diagonal: estudantes que atingem bons resultados em uma disciplina tendem a replicar o sucesso na outra, sugerindo que competências leitoras básicas estão sustentando o aprendizado matemático."
                        : "Os resultados apresentam uma dispersão mais pulverizada, indicando que uma parcela significativa de alunos possui habilidades bem desenvolvidas em uma área específica, mas apresenta lacunas que precisam ser diagnosticadas na outra.";

                    analysisContainer.innerHTML = `
                        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.25rem;">
                            <h4 style="color: #0f172a; font-size: 1.05rem; font-weight: 700; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                                Análise Aprofundada da Dispersão (${escapeHtml(selectedYear)})
                            </h4>
                            <p style="color: #475569; font-size: 0.95rem; line-height: 1.6; margin: 0 0 0.75rem 0;">
                                O diagrama acima reflete o cruzamento analítico das proficiências médias. ${trendText} ${correlationText}
                            </p>
                            <p style="color: #475569; font-size: 0.95rem; line-height: 1.6; margin: 0;">
                                <strong>Detalhamento dos quadrantes:</strong> Cerca de <strong>${percentQ1}%</strong> dos dados avaliados encontram-se no quadrante de alta performance (acima da média do grupo em ambas as disciplinas), enquanto <strong>${percentQ3}%</strong> concentram-se no quadrante de atenção prioritária (abaixo da média em ambas), demandando intervenções e estratégias intensivas de recomposição de aprendizagem conjunta.
                            </p>
                        </div>
                    `;
                } else {
                    analysisContainer.innerHTML = '';
                }
            }
        };

        // SEÇÃO 4: Adequação e Barras Empilhadas Verticais
        const barYears = [...new Set((data.adequacy || []).map(row => row.ano))].sort();
        const mockBars = (subject) => barYears.map(y => {
            const rows = data.adequacy.filter(row => row.ano === y && row.materia?.toLowerCase().includes(subject));
            const byLevel = [4, 3, 2, 1].map(level =>
                rows.filter(row => parseInt(row.adequacao, 10) === level)
                    .reduce((sum, row) => sum + row.percentual, 0));
            const total = byLevel.reduce((sum, value) => sum + value, 0) || 1;
            const [av, pr, ba, ins] = byLevel.map(value => value * 100 / total);
            return `
                <div style="flex: 1; max-width: 80px; min-width: 40px; display: flex; flex-direction: column; height: 300px; justify-content: flex-end; position: relative; z-index: 1;">
                    ${av > 0 ? `<div style="height: ${av}%; background: #3b82f6; color: #fff; font-size: 0.7rem; font-weight: 700; display: flex; align-items: center; justify-content: center; width: 100%;"><span>${av.toFixed(1)}%</span></div>` : ''}
                    ${pr > 0 ? `<div style="height: ${pr}%; background: #84cc16; color: #fff; font-size: 0.7rem; font-weight: 700; display: flex; align-items: center; justify-content: center; width: 100%;"><span>${pr.toFixed(1)}%</span></div>` : ''}
                    ${ba > 0 ? `<div style="height: ${ba}%; background: #eab308; color: #fff; font-size: 0.7rem; font-weight: 700; display: flex; align-items: center; justify-content: center; width: 100%;"><span>${ba.toFixed(1)}%</span></div>` : ''}
                    ${ins > 0 ? `<div style="height: ${ins}%; background: #ef4444; color: #fff; font-size: 0.7rem; font-weight: 700; display: flex; align-items: center; justify-content: center; width: 100%;"><span>${ins.toFixed(1)}%</span></div>` : ''}
                    <div style="position: absolute; bottom: -25px; width: 100%; text-align: center; font-size: 0.8rem; color: #475569; font-weight: 600;">${y}</div>
                </div>
            `;
        }).join('');

        const adeqHtml = `
            <div style="margin-bottom: 3rem;">
                <h3 style="font-size: 1.4rem; color: #1e3a8a; font-weight: 700; margin-bottom: 1rem;">Adequação</h3>
                <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; background: #fff; margin-bottom: 1rem;">
                    <p style="color: #475569; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;">Para facilitar a interpretação dos resultados das avaliações, o PAAEB classifica a proficiência dos alunos em <strong>quatro etapas de conhecimento</strong>:</p>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 1.5rem; font-size: 0.9rem;">
                        <thead style="background: #f8fafc; color: #64748b;">
                            <tr><th style="padding: 10px; text-align: left;">Etapa</th><th style="padding: 10px; text-align: left;">Significado</th><th style="padding: 10px; text-align: left;">Situação</th></tr>
                        </thead>
                        <tbody>
                            <tr><td style="padding: 10px; border-bottom: 1px solid #f1f5f9; text-align: center;">4</td><td style="padding: 10px; border-bottom: 1px solid #f1f5f9;">Conhecimento Avançado</td><td style="padding: 10px; border-bottom: 1px solid #f1f5f9; font-weight: 700;">Adequado</td></tr>
                            <tr style="background: #f8fafc;"><td style="padding: 10px; border-bottom: 1px solid #f1f5f9; text-align: center;">3</td><td style="padding: 10px; border-bottom: 1px solid #f1f5f9;">Conhecimento Proficiente</td><td style="padding: 10px; border-bottom: 1px solid #f1f5f9; font-weight: 700;">Adequado</td></tr>
                            <tr><td style="padding: 10px; border-bottom: 1px solid #f1f5f9; text-align: center;">2</td><td style="padding: 10px; border-bottom: 1px solid #f1f5f9;">Conhecimento Básico</td><td style="padding: 10px; border-bottom: 1px solid #f1f5f9; font-weight: 700; color: #64748b;">Inadequado</td></tr>
                            <tr style="background: #f8fafc;"><td style="padding: 10px; text-align: center;">1</td><td style="padding: 10px;">Conhecimento Insuficiente</td><td style="padding: 10px; font-weight: 700; color: #64748b;">Inadequado</td></tr>
                        </tbody>
                    </table>
                    <p style="color: #475569; font-size: 0.9rem;"><strong>Ou seja:</strong></p>
                    <ul style="color: #475569; font-size: 0.9rem; padding-left: 20px; line-height: 1.6;">
                        <li><strong>Etapas 3 e 4</strong> → o aluno <strong>atingiu o que era esperado</strong> ou está acima.</li>
                        <li><strong>Etapas 1 e 2</strong> → o aluno <strong>ainda não alcançou o esperado</strong>.</li>
                    </ul>
                    <p style="color: #475569; font-size: 0.9rem; margin-top: 1rem;">Com base nessa escala, o relatório mostra o <strong>percentual de alunos que atingiram ou superaram a etapa esperada</strong>, permitindo identificar o quanto a escola está conseguindo garantir o aprendizado previsto para cada série.</p>
                </div>
                
                <div style="display: flex; gap: 1rem; margin-bottom: 2rem;">
                    <div style="flex: 1; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; background: #fff;">
                        <h4 style="font-size: 1.4rem; color: #1e3a8a; font-weight: 700; margin-bottom: 1rem;">Como interpretar de forma rápida</h4>
                        <ul style="color: #475569; font-size: 0.9rem; padding-left: 20px; line-height: 1.6; margin-bottom: 1rem;">
                            <li>Quanto mais <strong>azul e verde</strong>, melhor o resultado da escola.</li>
                            <li>Quanto mais <strong>amarelo e vermelho</strong>, maior a necessidade de reforço pedagógico.</li>
                        </ul>
                        <p style="color: #475569; font-size: 0.9rem; line-height: 1.6;">Ao observar o gráfico, podemos <strong>ver a evolução ao longo dos anos</strong> e identificar se:</p>
                        <ul style="color: #475569; font-size: 0.9rem; padding-left: 20px; line-height: 1.6; margin-top: 1rem;">
                            <li>A aprendizagem está <strong>melhorando</strong>,</li>
                            <li>Se <strong>mantendo</strong>, ou</li>
                            <li><strong>Caindo</strong>.</li>
                        </ul>
                    </div>
                    <div style="flex: 1; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; background: #fff;">
                        <h4 style="font-size: 1.4rem; color: #1e3a8a; font-weight: 700; margin-bottom: 1rem;">Para que serve isso na prática</h4>
                        <p style="color: #475569; font-size: 0.9rem; line-height: 1.6; margin-bottom: 1rem;">Esses dados ajudam a escola a:</p>
                        <ul style="color: #475569; font-size: 0.9rem; padding-left: 20px; line-height: 1.6;">
                            <li><strong>Planejar ações de reforço</strong> para os alunos que estão nos níveis <strong>1 e 2</strong>;</li>
                            <li><strong>Fortalecer práticas</strong> que fizeram os alunos alcançar os níveis <strong>3 e 4</strong>;</li>
                            <li><strong>Acompanhar a evolução</strong> da aprendizagem ao longo do tempo.</li>
                        </ul>
                    </div>
                </div>

                <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; background: #fff; margin-bottom: 1.5rem; position: relative;">
                    <span style="position: absolute; top: 1rem; right: 1rem; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                    <h4 style="font-size: 1rem; color: #374151; font-weight: 700; margin-bottom: 0.5rem;">Matemática</h4>
                    <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 2rem;">
                        <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#3b82f6; margin-right:4px;"></span> 4. Avançado / Avanzado &nbsp;&nbsp;
                        <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#84cc16; margin-right:4px;"></span> 3. Proficiente / Satisfactorio &nbsp;&nbsp;
                        <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#eab308; margin-right:4px;"></span> 2. Básico / Regular &nbsp;&nbsp;
                        <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#ef4444; margin-right:4px;"></span> 1. Insuficiente
                    </div>
                    <div class="paaeb-bar-chart" style="display: flex; gap: 8px; justify-content: space-evenly; padding: 0 1rem; margin-left: 3rem; border-left: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; position: relative; z-index: 0;">
                        <!-- Y-axis percentuais -->
                        <div style="position: absolute; left: -10px; bottom: 0; transform: translateY(50%); font-size: 0.75rem; color: #64748b;">0%</div>
                        <div style="position: absolute; left: -15px; bottom: 20%; transform: translateY(50%); font-size: 0.75rem; color: #64748b;">20%</div>
                        <div style="position: absolute; left: -15px; bottom: 40%; transform: translateY(50%); font-size: 0.75rem; color: #64748b;">40%</div>
                        <div style="position: absolute; left: -15px; bottom: 60%; transform: translateY(50%); font-size: 0.75rem; color: #64748b;">60%</div>
                        <div style="position: absolute; left: -15px; bottom: 80%; transform: translateY(50%); font-size: 0.75rem; color: #64748b;">80%</div>
                        <div style="position: absolute; left: -20px; top: 0; transform: translateY(-50%); font-size: 0.75rem; color: #64748b;">100%</div>
                        <div style="position: absolute; left: -80px; top: 50%; transform: rotate(-90deg); font-size: 0.8rem; color: #64748b; font-weight: 700; width: 140px; text-align: center;">porcentaje_por_ano</div>
                        
                        <!-- Grid lines -->
                        <div style="position: absolute; left: 0; bottom: 20%; width: 100%; height: 1px; border-top: 1px dashed #e2e8f0; z-index: -1;"></div>
                        <div style="position: absolute; left: 0; bottom: 40%; width: 100%; height: 1px; border-top: 1px dashed #e2e8f0; z-index: -1;"></div>
                        <div style="position: absolute; left: 0; bottom: 60%; width: 100%; height: 1px; border-top: 1px dashed #e2e8f0; z-index: -1;"></div>
                        <div style="position: absolute; left: 0; bottom: 80%; width: 100%; height: 1px; border-top: 1px dashed #e2e8f0; z-index: -1;"></div>
                        
                        ${mockBars('matem')}
                    </div>
                    <div style="text-align: center; font-size: 0.8rem; color: #64748b; margin-top: 30px;">ano</div>
                </div>

                <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; background: #fff; position: relative;">
                    <span style="position: absolute; top: 1rem; right: 1rem; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                    <h4 style="font-size: 1rem; color: #374151; font-weight: 700; margin-bottom: 0.5rem;">Língua Portuguesa</h4>
                    <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 2rem;">
                        <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#3b82f6; margin-right:4px;"></span> 4. Avançado / Avanzado &nbsp;&nbsp;
                        <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#84cc16; margin-right:4px;"></span> 3. Proficiente / Satisfactorio &nbsp;&nbsp;
                        <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#eab308; margin-right:4px;"></span> 2. Básico / Regular &nbsp;&nbsp;
                        <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#ef4444; margin-right:4px;"></span> 1. Insuficiente
                    </div>
                    <div class="paaeb-bar-chart" style="display: flex; gap: 8px; justify-content: space-evenly; padding: 0 1rem; margin-left: 3rem; border-left: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; position: relative; z-index: 0;">
                        <!-- Y-axis percentuais -->
                        <div style="position: absolute; left: -10px; bottom: 0; transform: translateY(50%); font-size: 0.75rem; color: #64748b;">0%</div>
                        <div style="position: absolute; left: -15px; bottom: 20%; transform: translateY(50%); font-size: 0.75rem; color: #64748b;">20%</div>
                        <div style="position: absolute; left: -15px; bottom: 40%; transform: translateY(50%); font-size: 0.75rem; color: #64748b;">40%</div>
                        <div style="position: absolute; left: -15px; bottom: 60%; transform: translateY(50%); font-size: 0.75rem; color: #64748b;">60%</div>
                        <div style="position: absolute; left: -15px; bottom: 80%; transform: translateY(50%); font-size: 0.75rem; color: #64748b;">80%</div>
                        <div style="position: absolute; left: -20px; top: 0; transform: translateY(-50%); font-size: 0.75rem; color: #64748b;">100%</div>
                        <div style="position: absolute; left: -80px; top: 50%; transform: rotate(-90deg); font-size: 0.8rem; color: #64748b; font-weight: 700; width: 140px; text-align: center;">porcentaje_por_ano</div>
                        
                        <!-- Grid lines -->
                        <div style="position: absolute; left: 0; bottom: 20%; width: 100%; height: 1px; border-top: 1px dashed #e2e8f0; z-index: -1;"></div>
                        <div style="position: absolute; left: 0; bottom: 40%; width: 100%; height: 1px; border-top: 1px dashed #e2e8f0; z-index: -1;"></div>
                        <div style="position: absolute; left: 0; bottom: 60%; width: 100%; height: 1px; border-top: 1px dashed #e2e8f0; z-index: -1;"></div>
                        <div style="position: absolute; left: 0; bottom: 80%; width: 100%; height: 1px; border-top: 1px dashed #e2e8f0; z-index: -1;"></div>
                        
                        ${mockBars('portugues')}
                    </div>
                </div>
            </div>
        `;

        // SEÇÃO 5: Tabelas Finais (Nível x Escala) conforme nova imagem
        const finalTablesHtml = `
            <div style="margin-bottom: 2rem;">
                <h3 style="font-size: 1.4rem; color: #1e3a8a; font-weight: 700; margin-bottom: 1rem;">Distribuição Percentual dos Alunos na Escala de Proficiência</h3>
                <p style="color: #475569; font-size: 0.95rem; line-height: 1.6;">A tabela apresenta a distribuição dos alunos da escola nos diferentes níveis de proficiência em <strong>Língua Portuguesa</strong> e <strong>Matemática</strong>.</p>
                <p style="color: #475569; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">Cada nível indica o <strong>grau de domínio</strong> que o estudante possui em relação aos conteúdos esperados para a série.</p>
                
                <div style="border-bottom: 1px solid #cbd5e1; margin-bottom: 1.5rem;"></div>

                <div class="paaeb-fifth-explanation" ${data.serie === '5º ano' ? '' : 'hidden'}>
                <h4 style="font-size: 1.25rem; color: #1e3a8a; font-weight: 700; margin-bottom: 1rem;">Como interpretar os níveis no 5º ano</h4>
                <p style="color: #475569; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;">No 5º ano, a avaliação utiliza <strong>faixas de níveis específicas</strong>, considerando o <strong>estágio de desenvolvimento das crianças</strong>:</p>
                <ul style="color: #475569; font-size: 0.95rem; padding-left: 20px; line-height: 1.6; margin-bottom: 1rem;">
                    <li><strong>Língua Portuguesa</strong> → níveis 0 a 9</li>
                    <li><strong>Matemática</strong> → níveis 1 a 10</li>
                </ul>
                <p style="color: #475569; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">Esses níveis <strong>não correspondem a notas</strong>, e sim a <strong>etapas do processo de aprendizagem</strong>.</p>
                </div>
                
                <div style="border-bottom: 1px solid #cbd5e1; margin-bottom: 1.5rem;"></div>

                <h4 style="font-size: 1.25rem; color: #1e3a8a; font-weight: 700; margin-bottom: 1rem;">Significado da Escala de Adequação</h4>
                <div class="paaeb-scale-table"><table style="width: 100%; border-collapse: collapse; margin-bottom: 2rem; font-size: 0.85rem;">
                    <thead style="color: #64748b;">
                        <tr><th style="padding: 10px; text-align: left;">Situação do Aluno</th><th style="padding: 10px; text-align: left;">Significado</th><th style="padding: 10px; text-align: left;">Direcionamento para a Coordenação Pedagógica</th></tr>
                    </thead>
                    <tbody>
                        <tr><td style="padding: 10px; border-bottom: 1px solid #f1f5f9;">Avançado</td><td style="padding: 10px; border-bottom: 1px solid #f1f5f9;">Demonstra domínio seguro e autônomo dos conteúdos.</td><td style="padding: 10px; border-bottom: 1px solid #f1f5f9;">Organizar propostas de ampliação e aprofundamento para esses alunos.</td></tr>
                        <tr style="background: #f8fafc;"><td style="padding: 10px; border-bottom: 1px solid #f1f5f9;">Proficiente (No esperado)</td><td style="padding: 10px; border-bottom: 1px solid #f1f5f9;">Alcançou as aprendizagens previstas para a série.</td><td style="padding: 10px; border-bottom: 1px solid #f1f5f9;">Manter e fortalecer as práticas pedagógicas que sustentam esses resultados.</td></tr>
                        <tr><td style="padding: 10px;">Básico ou Insuficiente</td><td style="padding: 10px;">Ainda não consolidou aprendizagens essenciais.</td><td style="padding: 10px;">Planejar reforço contínuo, recuperação paralela e acompanhamento próximo junto aos docentes.</td></tr>
                    </tbody>
                </table></div>
                
                <div style="border-bottom: 1px solid #cbd5e1; margin-bottom: 1.5rem;"></div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="font-size: 1.25rem; color: #1e3a8a; font-weight: 700; margin: 0;">Como interpretar os percentuais apresentados</h4>
                    <select id="levelsYearSelect" style="border: 1px solid #e2e8f0; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; color: #64748b; background: #f8fafc; cursor: pointer; outline: none;">
                        ${scatterYearOptions || `<option value="">Sem dados</option>`}
                    </select>
                </div>
                <p style="color: #475569; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">A coluna <strong>Percentual (%)</strong> permite visualizar <strong>a proporção de alunos em cada nível</strong> para o ano selecionado.</p>
                
                <div id="paaebLevelsContainer"></div>
            </div>
        `;

        const drawLevelsTables = (selectedYear) => {
            const container = grid.querySelector('#paaebLevelsContainer');
            if (!container) return;

            const generateTableRows = (isMath) => {
                const subject = isMath ? 'matem' : 'portugues';
                const rows = (data.levels || []).filter(row => row.ano === selectedYear && row.materia?.toLowerCase().includes(subject));
                return rows.sort((a, b) => (parseInt(b.nivel_adq?.match(/\d+/)?.[0] || 0) - parseInt(a.nivel_adq?.match(/\d+/)?.[0] || 0)))
                    .map(row => {
                    const category = row.adequacao?.toLowerCase() || '';
                    const bg = category.includes('avan') ? '#dbeafe' : category.includes('profic') ? '#dcfce7' : category.includes('bás') ? '#fef9c3' : '#fee2e2';
                    return `
                        <tr>
                            <td style="padding: 12px; color: #475569; background: #f8fafc; border-right: 1px solid #fff;">${escapeHtml(row.nivel_adq)}</td>
                            <td style="padding: 12px; color: #475569; background: #f0fdfa; border-right: 1px solid #fff;">${escapeHtml(row.pontos_na_escala)}</td>
                            <td style="padding: 12px; background: ${bg}; color: #334155; border-right: 1px solid #fff;">${escapeHtml(row.adequacao)}</td>
                            <td style="padding: 12px; text-align: right; color: #475569; background: #f8fafc;">${format(row.percentual)}</td>
                        </tr>
                    `;
                }).join('');
            };

            const currentLevels = (data.levels || []).filter(row => row.ano === selectedYear);
            const grouped = {};
            currentLevels.forEach(row => {
                const key = `${row.materia}_${row.nivel_adq}`;
                if (!grouped[key]) grouped[key] = [];
                if (!grouped[key].find(g => g.pontos_na_escala === row.pontos_na_escala)) {
                    grouped[key].push(row);
                }
            });
            const conflicts = Object.values(grouped).filter(g => g.length > 1);
            let warningHtml = '';
            if (conflicts.length > 0) {
                const group = conflicts[0];
                const materia = group[0].materia.toLowerCase().includes('matem') ? 'Matemática' : 'Língua Portuguesa';
                const examples = group.map(row => `<li>A escola <strong>${escapeHtml(row.example_school || 'Exemplo')}</strong> usa a escala <em>${escapeHtml(row.pontos_na_escala)}</em> para o <strong>${escapeHtml(row.nivel_adq)}</strong>.</li>`).join('');
                warningHtml = `
                    <div style="background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem;">
                        <h4 style="color: #ef4444; font-size: 1.05rem; font-weight: 700; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 8px;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                            Atenção: Diferentes padrões de escala detectados
                        </h4>
                        <p style="color: #ef4444; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0.75rem;">Você está visualizando dados de múltiplas escolas simultaneamente. Algumas escolas utilizam <strong>padrões de escala diferentes</strong> para a mesma série, o que faz com que os níveis apareçam duplicados na tabela abaixo.</p>
                        <p style="color: #ef4444; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0.5rem;">Por exemplo, em ${materia}:</p>
                        <ul style="color: #ef4444; font-size: 0.95rem; padding-left: 20px; line-height: 1.6; margin-bottom: 1rem;">
                            ${examples}
                        </ul>
                        <p style="color: #ef4444; font-size: 0.95rem; line-height: 1.6;">Para visualizar a tabela de forma simplificada e sem duplicidades, selecione uma escola específica no filtro do topo da página.</p>
                    </div>
                `;
            }

            container.innerHTML = `
                ${warningHtml}
                <div style="display: flex; gap: 1rem;">
                    <div style="flex: 1; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; padding: 1.5rem; position: relative;">
                        <span style="position: absolute; top: 1rem; right: 1rem; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                        <h4 style="color: #64748b; font-size: 1rem; font-weight: 700; margin-bottom: 1rem;">Língua Portuguesa (${selectedYear})</h4>
                        <table style="width: 100%; border-collapse: separate; border-spacing: 0; text-align: left; font-size: 0.85rem;">
                            <thead>
                                <tr style="color: #3b82f6;">
                                    <th style="padding: 10px;">Nível</th><th style="padding: 10px;">Pontos na Escala</th><th style="padding: 10px;">Adequação</th><th style="padding: 10px; text-align: right;">Percentual (%)</th>
                                </tr>
                            </thead>
                            <tbody>${generateTableRows(false)}</tbody>
                        </table>
                    </div>
                    <div style="flex: 1; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; padding: 1.5rem; position: relative;">
                        <span style="position: absolute; top: 1rem; right: 1rem; color: #cbd5e1; letter-spacing: 1px; font-size: 0.7rem;">...</span>
                        <h4 style="color: #64748b; font-size: 1rem; font-weight: 700; margin-bottom: 1rem;">Matemática (${selectedYear})</h4>
                        <table style="width: 100%; border-collapse: separate; border-spacing: 0; text-align: left; font-size: 0.85rem;">
                            <thead>
                                <tr style="color: #3b82f6;">
                                    <th style="padding: 10px;">Nível</th><th style="padding: 10px;">Pontos na Escala</th><th style="padding: 10px;">Adequação</th><th style="padding: 10px; text-align: right;">Percentual (%)</th>
                                </tr>
                            </thead>
                            <tbody>${generateTableRows(true)}</tbody>
                        </table>
                    </div>
                </div>
            `;
        };

        grid.innerHTML = heroHtml + filterHtml + sinteseHtml + proficienciaHtml + distHtml + adeqHtml + finalTablesHtml;
        const historyPlot = grid.querySelector('.paaeb-history-plot');
        drawHistoryChart();
        if (historyPlot && typeof ResizeObserver !== 'undefined') {
            historyObserver = new ResizeObserver(drawHistoryChart);
            historyObserver.observe(historyPlot);
        }

        drawScatterChart(allScatterYears.includes(latestYear) ? latestYear : allScatterYears[0]);
        const scatterYearSelect = grid.querySelector('#scatterYearSelect');
        if (scatterYearSelect) {
            scatterYearSelect.addEventListener('change', (e) => {
                drawScatterChart(e.target.value);
            });
        }

        const levelsInitialYear = allScatterYears.includes(latestYear) ? latestYear : allScatterYears[0];
        drawLevelsTables(levelsInitialYear);
        const levelsYearSelect = grid.querySelector('#levelsYearSelect');
        if (levelsYearSelect) {
            levelsYearSelect.value = levelsInitialYear;
            levelsYearSelect.addEventListener('change', (e) => {
                drawLevelsTables(e.target.value);
            });
        }

        const unions = grid.querySelector('#paaebUniao');
        const associations = grid.querySelector('#paaebAssociacao');
        const schools = grid.querySelector('#paaebEscola');
        const serieSelect = grid.querySelector('#paaebSerie');
        const entities = data.entities || [];
        const addOptions = (select, rows) => {
            rows.forEach(([value, label]) => select.add(new Option(label, value)));
        };
        addOptions(unions, [...new Set(entities.map(row => row.uniao).filter(Boolean))].sort().map(value => [value, value]));
        unions.value = filters.uniao || '';
        const scopedAssociations = entities.filter(row => !unions.value || row.uniao === unions.value);
        addOptions(associations, [...new Set(scopedAssociations.map(row => row.associacao).filter(Boolean))].sort().map(value => [value, value]));
        associations.value = filters.associacao || '';
        addOptions(schools, scopedAssociations
            .filter(row => !associations.value || row.associacao === associations.value)
            .map(row => [String(row.id_escolas), row.escola])
            .sort((a, b) => a[1].localeCompare(b[1], 'pt-BR')));
        schools.value = filters.escola || '';
        addOptions(serieSelect, (data.series || []).map(value => [value, value]));
        serieSelect.value = data.serie || '';
        unions.addEventListener('change', () => loadPaaebDashboard({ uniao: unions.value, serie: serieSelect.value }));
        associations.addEventListener('change', () => loadPaaebDashboard({ uniao: unions.value, associacao: associations.value, serie: serieSelect.value }));
        schools.addEventListener('change', () => loadPaaebDashboard({ uniao: unions.value, associacao: associations.value, escola: schools.value, serie: serieSelect.value }));
        serieSelect.addEventListener('change', () => loadPaaebDashboard({ uniao: unions.value, associacao: associations.value, escola: schools.value, serie: serieSelect.value }));

        const shareBtn = grid.querySelector('#paaebShareBtn');
        if (shareBtn) {
            shareBtn.addEventListener('click', () => {
                const shareUrl = new URL(window.location.href);
                shareUrl.hash = 'paaeb';
                Object.entries(filters).forEach(([k, v]) => v ? shareUrl.searchParams.set(k, v) : shareUrl.searchParams.delete(k));
                navigator.clipboard.writeText(shareUrl.toString()).then(() => {
                    const originalHtml = shareBtn.innerHTML;
                    shareBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg> Link Copiado!';
                    setTimeout(() => shareBtn.innerHTML = originalHtml, 2000);
                });
            });
        }

        const exportBtn = grid.querySelector('#paaebExportPdfBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => { if(typeof App !== 'undefined') App.showToast('Em breve', 'info'); else alert('Em breve'); });
        }
    }
});
